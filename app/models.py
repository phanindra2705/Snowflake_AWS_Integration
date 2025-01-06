import snowflake.connector
import pandas as pd

from app import snowflake_user, snowflake_password, snowflake_warehouse, snowflake_account, snowflake_database, \
    snowflake_schema


import snowflake.connector
from app import get_snowflake_credentials

def create_users_table():
    """Create the users table in Snowflake."""
    try:
        # Fetch credentials dynamically
        credentials = get_snowflake_credentials()

        # Connect to Snowflake
        conn = snowflake.connector.connect(
            user=credentials["user"],
            password=credentials["password"],
            account=credentials["account"],
            warehouse=credentials["warehouse"],
            database=credentials["database"],
            schema=credentials["schema"]
        )
        cursor = conn.cursor()

        # Create table query
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTOINCREMENT,
            username STRING UNIQUE,
            password_hash STRING,
            gmail STRING UNIQUE,
            PRIMARY KEY (id)
        )
        """)
        conn.commit()
        print("Users table created successfully.")
    except Exception as e:
        print(f"Error creating users table: {e}")
    finally:
        cursor.close()
        conn.close()


def get_snowflake_tables():
    """Fetch the list of tables in the Snowflake database."""
    try:
        conn = snowflake.connector.connect(
            user=snowflake_user,
            password=snowflake_password,
            account=snowflake_account,
            warehouse=snowflake_warehouse,
            database=snowflake_database,
            schema=snowflake_schema
        )
        cursor = conn.cursor()

        cursor.execute("SHOW TABLES")
        tables = [row[1] for row in cursor.fetchall()]
        return tables
    except Exception as e:
        print(f"Error fetching tables: {str(e)}")
        return []
    finally:
        cursor.close()
        conn.close()


def fetch_table_data(table_name):
    """Fetch data from a specified Snowflake table."""
    try:
        # Fetch credentials dynamically
        credentials = get_snowflake_credentials()

        # Connect to Snowflake
        conn = snowflake.connector.connect(
            user=credentials["user"],
            password=credentials["password"],
            account=credentials["account"],
            warehouse=credentials["warehouse"],
            database=credentials["database"],
            schema=credentials["schema"]
        )
        cursor = conn.cursor()

        # Execute query
        cursor.execute(f"SELECT * FROM {table_name}")
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        return pd.DataFrame(rows, columns=columns)
    except Exception as e:
        print(f"Error fetching data from table {table_name}: {e}")
        return None
    finally:
        cursor.close()
        conn.close()



def create_import_table(username, table_name, dataframe):
    """Create a table and insert data from a DataFrame."""
    try:
        conn = snowflake.connector.connect(
            user=snowflake_user,
            password=snowflake_password,
            account=snowflake_account,
            warehouse=snowflake_warehouse,
            database=snowflake_database,
            schema=snowflake_schema
        )
        cursor = conn.cursor()

        # Create table query
        columns = ", ".join(f"{col} STRING" for col in dataframe.columns)
        cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({columns})")

        # Insert data into the table
        for _, row in dataframe.iterrows():
            values = ", ".join(f"'{str(value)}'" for value in row)
            cursor.execute(f"INSERT INTO {table_name} VALUES ({values})")

        conn.commit()
        print(f"Table '{table_name}' created and data inserted successfully.")
        return True
    except Exception as e:
        print(f"Error creating table {table_name}: {str(e)}")
        return False
    finally:
        cursor.close()
        conn.close()
