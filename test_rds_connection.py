import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
import os

load_dotenv()

# Load credentials
HOST = os.getenv('DB_HOST')
PORT = os.getenv('DB_PORT')
USER = os.getenv('DB_USER')
PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')  # should be "shoelala"

def create_database_if_not_exists():
    try:
        # Step 1: Connect to default 'postgres' database
        conn = psycopg2.connect(
            host=HOST,
            port=PORT,
            database="postgres",  # default db
            user=USER,
            password=PASSWORD,
            sslmode='require'
        )
        conn.autocommit = True
        cursor = conn.cursor()

        # Step 2: Check if our database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (DB_NAME,))
        exists = cursor.fetchone()

        if not exists:
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DB_NAME)))
            print(f"✅ Database '{DB_NAME}' created successfully!")
        else:
            print(f"ℹ️ Database '{DB_NAME}' already exists.")

        cursor.close()
        conn.close()

        # Step 3: Test connection to the target database
        test_connection()

    except Exception as e:
        print(f"❌ Error: {e}")

def test_connection():
    try:
        conn = psycopg2.connect(
            host=HOST,
            port=PORT,
            database=DB_NAME,
            user=USER,
            password=PASSWORD,
            sslmode='require'
        )
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ Connection successful! PostgreSQL version: {version[0]}")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"❌ Connection test failed: {e}")

if __name__ == "__main__":
    create_database_if_not_exists()
