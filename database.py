import os
import psycopg2
import random
from dotenv import load_dotenv
from urllib.parse import urlparse

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

def get_random_transcription():
    conn = get_database_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, transcription FROM transcriptions WHERE valid = true")
    transcriptions = cur.fetchall()

    if not transcriptions:
        cur.close()
        conn.close()
        return None

    random_transcription = random.choice(transcriptions)
    transcription_id = random_transcription[0]
    transcription = random_transcription[1]

    cur.close()
    conn.close()

    return {"id": transcription_id, "transcription": transcription}

def invalidate_transcription(transcription_id):
    conn = get_database_connection()
    cur = conn.cursor()

    query = "UPDATE transcriptions SET valid = false WHERE id = %s"
    cur.execute(query, (transcription_id,))
    conn.commit()

    cur.close()
    conn.close()

def add_transcription_on(transcription):

    if not transcription:
        return False, "Nenhuma transcrição fornecida."

    if transcription_exists(transcription):
        return False, "A transcrição já existe no banco de dados."

    try:
        conn = get_database_connection()
        cur = conn.cursor()

        query = "INSERT INTO transcriptions (transcription, valid) VALUES (%s, %s)"
        cur.execute(query, (transcription, True))

        conn.commit()
        cur.close()
        conn.close()

        return True, "Transcrição adicionada com sucesso."

    except Exception as e:
        return False, f"Erro ao adicionar transcrição: {str(e)}"


def transcription_exists(transcription):
    try:
        conn = get_database_connection()
        cur = conn.cursor()

        query = "SELECT COUNT(*) FROM transcriptions WHERE transcription = %s"
        cur.execute(query, (transcription,))
        count = cur.fetchone()[0]

        cur.close()
        conn.close()

        return count > 0

    except Exception as e:
        return False
