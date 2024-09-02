import os
import psycopg2
import random
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
        return False, f"Erro ao adicionar transcrição"


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


def create_table_if_not_exists():
    try:
        conn = get_database_connection()
        cur = conn.cursor()

        # Verifica se a tabela existe
        cur.execute("""
        SELECT EXISTS (
            SELECT FROM pg_tables
            WHERE tablename  = 'transcriptions'
        );
        """)

        exists = cur.fetchone()[0]

        if not exists:
            # Cria a tabela se ela não existir
            cur.execute("""
            CREATE TABLE transcriptions (
                id SERIAL PRIMARY KEY,
                transcription TEXT NOT NULL,
                valid BOOLEAN DEFAULT TRUE
            );
            """)
            conn.commit()

        cur.close()
        conn.close()

    except Exception as e:
        print(f"Erro ao criar tabela: {str(e)}")