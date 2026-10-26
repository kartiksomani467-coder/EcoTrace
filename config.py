
import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "ecotrace_db"),
}

def validate_config():
    """Check whether the required database settings are present."""
    required = ["host", "port", "user", "password", "database"]
    missing = [key for key in required if not DB_CONFIG.get(key)]

    if missing:
        raise ValueError(
            "Missing database configuration: "
            + ", ".join(missing)
            + ". Check your .env file."
        )

if __name__ == "__main__":
    validate_config()
    print("EcoTrace configuration loaded successfully.")
    print(f"Database host: {DB_CONFIG['host']}")
    print(f"Database name: {DB_CONFIG['database']}")
    print("Database password: [hidden]")
