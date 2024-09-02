import os
import psycopg2
from dotenv import load_dotenv
import urllib.parse as urlparse

load_dotenv()


def get_database_connection():
    url = urlparse.urlparse(os.getenv("DATABASE_URL"))

    conn = psycopg2.connect(
        database=url.path[1:],
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port
    )
    return conn