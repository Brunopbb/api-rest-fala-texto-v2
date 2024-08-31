import os

import psycopg2
import random
from dotenv import load_dotenv
import urllib.parse as urlparse


def get_database_connection():
    url = urlparse.urlparse(os.environ['DATABASE_URL'])

    conn = psycopg2.connect(
        database=url.path[1:],
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port
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
