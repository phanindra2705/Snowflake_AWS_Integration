from flask import Flask
import boto3
import json
from flask_mail import Mail


# Flask app initialization
app = Flask(__name__)

# Flask-Mail Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'phanindranaidu222@gmail.com'  # Replace with your email
app.config['MAIL_PASSWORD'] = 'yxpc vbeg gyhr bdhl'  # Replace with your app password
app.config['MAIL_DEFAULT_SENDER'] = ('Export Import', 'phanindranaidu222@gmail.com')
app.config['MAIL_DEBUG'] = True


mail = Mail(app)

# Configurations
app.secret_key = 'aws/secretsmanager'  # Replace with a secure key
app.config['SESSION_TYPE'] = 'filesystem'  # Use filesystem for session storage

# AWS S3 Configuration
s3_bucket_name = 'testingsnowflakebucketwithpython'  # Replace with your bucket name
s3 = boto3.client('s3', region_name='us-east-2')  # Replace with your region


# Function to fetch secrets from AWS Secrets Manager
def get_snowflake_credentials():
    """Fetch Snowflake credentials from AWS Secrets Manager."""
    secret_name = "myApp/snowflake"  # Replace with your secret name
    region_name = "us-east-2"  # Replace with your AWS region

    client = boto3.client("secretsmanager", region_name=region_name)

    try:
        response = client.get_secret_value(SecretId=secret_name)
        secret = json.loads(response["SecretString"])

        # Validate required keys
        required_keys = [
            "user", "password", "account", "warehouse", "database", "schema"
        ]
        for key in required_keys:
            if key not in secret:
                raise KeyError(f"Missing key in secret: {key}")


        return {
            "user": secret["user"],
            "password": secret["password"],
            "account": secret["account"],
            "warehouse": secret["warehouse"],
            "database": secret["database"],
            "schema": secret["schema"]
        }
    except Exception as e:
        print(f"Error fetching Snowflake credentials: {e}")
        raise


# Fetch Snowflake credentials and expose them
try:
    snowflake_credentials = get_snowflake_credentials()
    snowflake_user = snowflake_credentials["user"]
    snowflake_password = snowflake_credentials["password"]
    snowflake_account = snowflake_credentials["account"]
    snowflake_warehouse = snowflake_credentials["warehouse"]
    snowflake_database = snowflake_credentials["database"]
    snowflake_schema = snowflake_credentials["schema"]
except Exception as e:
    print(f"Failed to retrieve Snowflake credentials: {e}")
    # Optional: Exit the application if credentials cannot be retrieved
    exit(1)
