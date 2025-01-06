from flask import Flask, jsonify, request, session, redirect, url_for, flash, render_template
from app import app, s3, s3_bucket_name, snowflake_user, snowflake_password, snowflake_account, snowflake_warehouse, snowflake_database, snowflake_schema
from models import create_users_table, get_snowflake_tables, fetch_table_data, create_import_table
from utils import upload_to_s3
from email_utils import send_email
import snowflake.connector
import pandas as pd
import time
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

# Session lifetime
app.permanent_session_lifetime = timedelta(minutes=30)

# -------------------------
# Page Routes
# -------------------------


@app.route('/', methods=['GET'])
def home():
    """Redirect to signup page."""
    return redirect(url_for('signup_page'))


@app.route('/signup', methods=['GET'])
def signup_page():
    """Serve the signup page."""
    return render_template('signup.html')


@app.route('/signin', methods=['GET'])
def signin_page():
    """Serve the signin page."""
    return render_template('signin.html')


@app.route('/dashboard', methods=['GET'])
def dashboard_page():
    """Serve the dashboard page."""
    if 'username' not in session:
        return redirect(url_for('signin_page'))
    return render_template('dashboard.html')


@app.route('/export', methods=['GET'])
def export_page():
    """Serve the export data page."""
    if 'username' not in session:
        return redirect(url_for('signin_page'))
    return render_template('index_export.html')


@app.route('/import', methods=['GET'])
def import_page():
    """Serve the import data page."""
    if 'username' not in session:
        return redirect(url_for('signin_page'))
    return render_template('index_import.html')

# -------------------------
# API Endpoints
# -------------------------


@app.route('/api/signup', methods=['POST'])
def signup_api():
    """API for user signup."""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    gmail = data.get('gmail')

    if not username or not password or not gmail:
        return jsonify({'error': 'All fields are required'}), 400

    if not gmail.endswith('@gmail.com'):
        return jsonify({'error': 'Email must be a Gmail address'}), 400

    password_hash = generate_password_hash(password)

    try:
        create_users_table()
        conn = snowflake.connector.connect(
            user=snowflake_user,
            password=snowflake_password,
            account=snowflake_account,
            warehouse=snowflake_warehouse,
            database=snowflake_database,
            schema=snowflake_schema
        )
        cursor = conn.cursor()

        cursor.execute("SELECT 1 FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            return jsonify({'error': 'Username already exists'}), 400

        cursor.execute("INSERT INTO users (username, password_hash, gmail) VALUES (%s, %s, %s)",
                       (username, password_hash, gmail))
        conn.commit()

        session['username'] = username
        session['user_email'] = gmail
        return jsonify({'message': 'Signup successful!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/signin', methods=['POST'])
def signin_api():
    """API for user signin."""
    data = request.get_json()
    login = data.get('login')  # Can be username or email
    password = data.get('password')

    try:
        # Connect to Snowflake and retrieve user details
        conn = snowflake.connector.connect(
            user=snowflake_user,
            password=snowflake_password,
            account=snowflake_account,
            warehouse=snowflake_warehouse,
            database=snowflake_database,
            schema=snowflake_schema
        )
        cursor = conn.cursor()

        cursor.execute("SELECT username, password_hash, gmail FROM users WHERE username = %s OR gmail = %s", (login, login))
        result = cursor.fetchone()

        if result:
            stored_username, stored_password_hash, stored_email = result
            if check_password_hash(stored_password_hash, password):
                session['username'] = stored_username
                session['user_email'] = stored_email  # Set the email in the session
                print(f"[DEBUG] User signed in: {stored_username}, Email: {stored_email}")
                return jsonify({'message': 'Signin successful', 'username': stored_username}), 200
            else:
                return jsonify({'error': 'Invalid credentials'}), 401
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/dashboard', methods=['GET'])
def dashboard_api():
    """API to fetch dashboard data."""
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    success_message = session.pop('success_message', None)
    return jsonify({'username': session['username'], 'success_message': success_message})


@app.route('/api/tables', methods=['GET'])
def get_tables_api():
    """API to fetch Snowflake tables."""
    try:
        tables = get_snowflake_tables()
        return jsonify({'tables': tables}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/s3_files', methods=['GET'])
def list_s3_files_api():
    """API to list S3 CSV files."""
    try:
        response = s3.list_objects_v2(Bucket=s3_bucket_name)
        csv_files = [content['Key'] for content in response.get('Contents', []) if content['Key'].endswith('.csv')]
        return jsonify(csv_files), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/export', methods=['POST'])
def export_data_api():
    """API to export table data to S3 and send email notification."""
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    table_name = data.get('table_name')

    if not table_name:
        return jsonify({'error': 'Table name is required'}), 400

    try:
        start_time = time.time()
        table_data = fetch_table_data(table_name)
        if table_data is None:
            return jsonify({'error': 'Error fetching table data'}), 500

        csv_content = table_data.to_csv(index=False)
        now = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        file_name = f"{table_name}_{now}.csv"

        if upload_to_s3(csv_content, file_name):
            duration = time.time() - start_time
            success_message = f"File '{file_name}' uploaded to S3 in {duration:.2f} seconds"
            print(f"[DEBUG] Success message: {success_message}")

            # Send email notification
            recipient_email = session.get('user_email')
            if not recipient_email:
                print("[ERROR] Recipient email not found in session.")
                return jsonify({'error': 'Recipient email not found'}), 400

            print(f"[DEBUG] Preparing to send email to {recipient_email}...")
            subject = "Data Export Notification"
            email_body = f"Dear {session['username']},\n\n{success_message}.\n\nThank you."
            email_sent = send_email(subject, recipient_email, email_body)

            if not email_sent:
                print("[ERROR] Failed to send email notification.")
            else:
                print("[DEBUG] Email notification sent successfully.")

            return jsonify({'message': success_message}), 200
        else:
            return jsonify({'error': 'Error uploading file to S3'}), 500
    except Exception as e:
        print(f"[ERROR] General error: {e}")
        return jsonify({'error': f"General error: {str(e)}"}), 500


@app.route('/api/import', methods=['POST'])
def import_data_api():
    """API to import data from S3 to Snowflake and send email notification."""
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    s3_file_key = data.get('s3_file_key')

    if not s3_file_key:
        return jsonify({'error': 'S3 file key is required'}), 400

    try:
        start_time = time.time()
        local_file_path = '/tmp/temp_file.csv'

        # Download the file from S3
        print(f"[DEBUG] Downloading file '{s3_file_key}' from S3 bucket '{s3_bucket_name}'...")
        s3.download_file(s3_bucket_name, s3_file_key, local_file_path)
        print("[DEBUG] File downloaded successfully.")

        # Read the CSV file into a DataFrame
        print("[DEBUG] Reading file into DataFrame...")
        df = pd.read_csv(local_file_path)
        print("[DEBUG] DataFrame created successfully.")

        # Generate table name based on username and file key
        table_name = f"{s3_file_key.split('.')[0]}_{session['username']}".replace("-", "_")

        # Create table and insert data into Snowflake
        print(f"[DEBUG] Creating table '{table_name}' in Snowflake...")
        if create_import_table(session['username'], table_name, df):
            duration = time.time() - start_time
            success_message = f"Data from '{s3_file_key}' imported into table '{table_name}' in {duration:.2f} seconds."
            print(f"[DEBUG] Success message: {success_message}")

            # Send email notification
            recipient_email = session.get('user_email')
            if not recipient_email:
                print("[ERROR] Recipient email not found in session.")
                return jsonify({'error': 'Recipient email not found'}), 400

            print(f"[DEBUG] Preparing to send email to {recipient_email}...")
            subject = "Data Import Notification"
            email_body = f"Dear {session['username']},\n\n{success_message}.\n\nThank you."
            email_sent = send_email(subject, recipient_email, email_body)

            if not email_sent:
                print("[ERROR] Failed to send email notification.")
            else:
                print("[DEBUG] Email notification sent successfully.")

            return jsonify({'message': success_message}), 200
        else:
            return jsonify({'error': 'Failed to create table in Snowflake'}), 500

    except Exception as e:
        print(f"[ERROR] General error during import: {e}")
        return jsonify({'error': f"General error: {str(e)}"}), 500


@app.route('/logout', methods=['POST'])
def logout():
    """API to log out a user."""
    try:
        session.pop('username', None)
        session.pop('user_email', None)
        return jsonify({'message': 'Logged out successfully'}), 200
    except Exception as e:
        print(f"Error during logout: {e}")
        return jsonify({'error': 'An error occurred during logout'}), 500


@app.route('/logout', methods=['GET'])
def logout_get():
    """Redirect to signin page after logout."""
    session.pop('username', None)
    session.pop('user_email', None)
    flash('You have been logged out.')
    return redirect(url_for('signin_page'))


# Run the application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)
