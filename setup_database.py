
import re
from pathlib import Path

from db import get_connection


def main():
    schema_path = Path(__file__).parent / "schema.sql"

    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    sql_script = schema_path.read_text(encoding="utf-8")

    # Remove full-line SQL comments before splitting statements.
    sql_script = re.sub(
        r"(?m)^\s*--.*?$",
        "",
        sql_script
    )

    statements = [
        statement.strip()
        for statement in sql_script.split(";")
        if statement.strip()
    ]

    connection = get_connection()
    cursor = connection.cursor()

    try:
        for number, statement in enumerate(statements, start=1):
            try:
                cursor.execute(statement)
            except Exception as exc:
                raise RuntimeError(
                    f"SQL statement {number} failed:\n{exc}\n\n"
                    f"Statement:\n{statement}"
                ) from exc

        cursor.execute("SELECT DATABASE()")
        database_name = cursor.fetchone()[0]

        if database_name != "ecotrace_db":
            raise RuntimeError(
                f"Unexpected database selected: {database_name}"
            )

        cursor.execute("SHOW TABLES")
        tables = [row[0] for row in cursor.fetchall()]

        expected_tables = {
            "categories",
            "items",
            "inventory_batches",
            "usage_logs",
            "stock_movements",
            "suppliers",
            "purchases",
            "purchase_items",
            "app_settings",
        }

        missing_tables = expected_tables - set(tables)

        if missing_tables:
            raise RuntimeError(
                "Schema verification failed. Missing tables: "
                + ", ".join(sorted(missing_tables))
            )

        print("EcoTrace schema created and verified!")
        print(f"Database: {database_name}")
        print(f"Tables verified: {len(expected_tables)}")

        for table in sorted(expected_tables):
            print(f"- {table}")

        cursor.execute("SELECT COUNT(*) FROM app_settings")
        print(f"Default settings: {cursor.fetchone()[0]}")

    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    main()
