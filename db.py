import mysql.connector
from config import DB_CONFIG
import os

def get_db_connection():
    return mysql.connector.connect(
        host=DB_CONFIG["host"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        database=DB_CONFIG["database"]
    )

def initialize_database():
    """Run schema.sql on first app launch (only when tables don't exist)."""

    # Connect without selecting a database to allow CREATE DATABASE
    conn = mysql.connector.connect(
        host=DB_CONFIG["host"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"]
    )
    cursor = conn.cursor()

    # Create DB if not exists
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
    conn.commit()
    cursor.close()
    conn.close()

    # Now connect to the database
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if a table exists (e.g., users table)
    cursor.execute("""
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_schema = %s AND table_name = 'users'
    """, (DB_CONFIG['database'],))

    exists = cursor.fetchone()[0]

    if exists == 0:
        # Run schema.sql
        print("Initializing database using schema.sql ...")
        with open("schema.sql", "r") as f:
            sql_script = f.read()

        # Execute SQL script safely
        for statement in sql_script.split(";"):
            if statement.strip():
                cursor.execute(statement + ";")

        conn.commit()

    cursor.close()
    conn.close()
