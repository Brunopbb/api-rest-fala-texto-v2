import os
import psycopg2
import random
from database_connection import *


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

    return True

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
        return False, f"Erro ao adicionar transcrição:"


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

def list_valid_transcriptions():
    try:
        conn = get_database_connection()
        cur = conn.cursor()

        query = "SELECT id, transcription FROM transcriptions WHERE valid = true"
        cur.execute(query)
        transcriptions = cur.fetchall()

        cur.close()
        conn.close()

        return [{"id": row[0], "transcription": row[1]} for row in transcriptions]

    except Exception as e:
        print(f"Erro ao listar transcrições: {str(e)}")
        return []

def delete_transcription(transcription_id):
    try:
        conn = get_database_connection()
        cur = conn.cursor()

        query = "DELETE FROM transcriptions WHERE id = %s"
        cur.execute(query, (transcription_id,))
        conn.commit()

        cur.close()
        conn.close()

        return True

    except Exception as e:
        print(f"Erro ao deletar transcrição: {str(e)}")
        return False

def get_transcription_id(transcription):
    try:
        conn = get_database_connection()
        cur = conn.cursor()

        query = "SELECT id FROM transcriptions WHERE transcription = %s AND valid = true"
        cur.execute(query, (transcription,))
        result = cur.fetchone()

        cur.close()
        conn.close()

        if result:
            return result[0]  # Retorna o ID da transcrição
        else:
            return None  # Caso a transcrição não seja encontrada ou já tenha sido invalidada

    except Exception as e:
        print(f"Erro ao obter ID da transcrição: {str(e)}")
        return None

