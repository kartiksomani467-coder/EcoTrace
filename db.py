
import mysql.connector
from mysql.connector import Error

from config import DB_CONFIG, validate_config


def get_connection():
    """Create and return a connection to the EcoTrace database."""
    validate_config()

    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as exc:
        raise RuntimeError(
            f"Could not connect to the EcoTrace database: {exc}"
        ) from exc


if __name__ == "__main__":
    try:
        connection = get_connection()

        cursor = connection.cursor()
        cursor.execute("SELECT DATABASE(), VERSION()")
        database_name, mysql_version = cursor.fetchone()

        print("EcoTrace database connection successful!")
        print(f"Database: {database_name}")
        print(f"MySQL version: {mysql_version}")

        cursor.close()
        connection.close()
        print("Connection closed successfully.")

    except (Error, RuntimeError, ValueError) as exc:
        print(f"Connection test failed: {exc}")
