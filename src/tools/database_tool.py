import pandas as pd
from sqlalchemy import create_engine, text
import os


class DatabaseTool:
    def __init__(self):
        db_user = os.getenv("DB_USER", "postgres")
        db_pass = os.getenv("DB_PASS", "2323")
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "5432")
        db_name = os.getenv("DB_NAME", "tariff_db")

        self.engine = create_engine(
            f"postgresql+psycopg2://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
        )

    def import_excel_to_db(self, excel_path: str, table_name="tariff_data"):
        """Load Excel into PostgreSQL"""
        df = pd.read_excel(excel_path)
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
        df.to_sql(table_name, self.engine, if_exists="replace", index=False)
        print(f"✅ Imported {len(df)} rows into '{table_name}' table")

    def get_row_by_hscode(self, input_hscode: str, table_name="tariff_data"):
        """Retrieve a row by HSCode"""
        query = text(f"SELECT * FROM {table_name} WHERE hscode = :hscode")
        with self.engine.connect() as conn:
            result = conn.execute(query, {"hscode": input_hscode}).fetchone()
        if result:
            return dict(result._mapping)
        return None
