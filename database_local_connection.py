from dotenv import load_dotenv
import os
import psycopg2

load_dotenv()

postegress_db = os.getenv("POSTGRES_DB")
postegress_user = os.getenv("POSTGRES_USER")
postegress_pass = os.getenv("POSTGRES_PASSWORD")

def get_database_connection():
    conn = psycopg2.connect(
        database=postegress_db,
        user=postegress_user,
        password=postegress_pass,
        host="db",
        port=5432
    )
    return conn