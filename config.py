
import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()


def get_setting(key, default=None):
    """Use Streamlit Cloud secrets, falling back to local environment variables."""
    try:
        value = st.secrets.get(key)
        if value is not None:
            return value
    except Exception:
        pass

    return os.getenv(key, default)


DB_CONFIG = {
    "host": get_setting("DB_HOST", "127.0.0.1"),
    "port": int(get_setting("DB_PORT", "3306")),
    "user": get_setting("DB_USER", "root"),
    "password": get_setting("DB_PASSWORD", ""),
    "database": get_setting("DB_NAME", "ecotrace_db"),
    "ssl_disabled": False,
}


def validate_config():
    required = ["host", "port", "user", "password", "database"]
    missing = [key for key in required if not DB_CONFIG.get(key)]

    if missing:
        raise ValueError(
            "Missing database configuration: "
            + ", ".join(missing)
            + ". Check Streamlit Secrets or your local .env file."
        )


if __name__ == "__main__":
    validate_config()
    print("EcoTrace configuration loaded successfully.")
    print(f"Database host: {DB_CONFIG['host']}")
    print(f"Database name: {DB_CONFIG['database']}")
    print("Database password: [hidden]")
