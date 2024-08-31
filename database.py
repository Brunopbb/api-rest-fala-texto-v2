import os

import psycopg2
import random
from dotenv import load_dotenv

load_dotenv(dotenv_path='.env')

POSTGRES_USER=os.getenv('POSTGRES_USER')
POSTGRES_PASSWORD=os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB=os.getenv('POSTGRES_DB')
postgresql_host = os.getenv("POSTGRESQL_HOST")
print(postgresql_host)
def get_database_connection():
    conn = psycopg2.connect(
        host=postgresql_host,
        database=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD

    )

    return conn

def get_random_transcription():
    conn = get_database_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM transcriptions")
    transcriptions = cur.fetchall()

    query = "UPDATE transcriptions SET valid = false WHERE id = %s"

    while True:
        random_transcription = random.choice(transcriptions)
        id_bd = random_transcription[0]
        transcription = random_transcription[1]
        valid = random_transcription[2]

        if valid:
            cur.execute(query, (id_bd,))
            conn.commit()
            break

    cur.close()
    conn.close()

    return transcription
