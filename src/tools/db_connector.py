import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()


def get_tariff_connection(test: bool = False):
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("TARIFF_DATABASE_NAME"),
            user=os.getenv("TARIFF_DATABASE_USER"),
            password=os.getenv("TARIFF_DATABASE_PASSWORD"),
            host=os.getenv("TARIFF_DATABASE_HOST"),
            port=os.getenv("TARIFF_DATABASE_PORT"),
        )

        print("---> Tariff database connected successfully!")

        if test:
            with conn.cursor() as cur:
                cur.execute("SELECT NOW();")
                print("---> Tariff DB Time:", cur.fetchone()[0])

        return conn

    except Exception as e:
        print("---> Failed to connect Tariff DB")
        print("Error:", e)
        return None


def get_valuation_connection(test: bool = False):
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("EVALUATION_DATABASE_NAME"),
            user=os.getenv("EVALUATION_DATABASE_USER"),
            password=os.getenv("EVALUATION_DATABASE_PASSWORD"),
            host=os.getenv("EVALUATION_DATABASE_HOST"),
            port=os.getenv("EVALUATION_DATABASE_PORT"),
        )

        print("---> Valuation database connected successfully!")

        if test:
            with conn.cursor() as cur:
                cur.execute("SELECT NOW();")
                print("---> Valuation DB Time:", cur.fetchone()[0])

        return conn

    except Exception as e:
        print("---> Failed to connect Valuation DB")
        print("Error:", e)
        return None
