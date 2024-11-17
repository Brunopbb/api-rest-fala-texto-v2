from flask import Flask, jsonify, render_template, request
from huggingface_hub import login
from datasets import Dataset, Audio, load_dataset, concatenate_datasets, DatasetDict
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from dotenv import load_dotenv
from pydub import AudioSegment
import os
import io
import soundfile as sf
import json
from database import *

app = Flask(__name__)
CORS(app)

load_dotenv()
huggingface_token = os.getenv("HUGGINGFACE_TOKEN")
huggingface_id = os.getenv("HUGGINGFACE_REPO_ID")

login(huggingface_token)

create_table_if_not_exists()

LOCAL_DATA_FILE = "local_data.json"



scheduler = BackgroundScheduler()
scheduler.start()

def initialize_local_data_file():
    """
    Ensures that the local data file exists and is properly initialized.
    """
    if not os.path.exists(LOCAL_DATA_FILE):
        try:
            with open(LOCAL_DATA_FILE, "w") as file:
                json.dump({"audio": [], "transcription": []}, file)
            print(f"Local data file '{LOCAL_DATA_FILE}' created successfully.")
        except Exception as e:
            print(f"Error creating local data file: {e}")
            raise

initialize_local_data_file()
def sync_data_with_huggingface():
    """
    Synchronizes locally stored data with the Hugging Face dataset.
    """
    with open(LOCAL_DATA_FILE, "r+") as file:
        local_data = json.load(file)

        if not local_data["audio"]:
            return  # Nothing to sync

        new_data = Dataset.from_dict(local_data)
        new_data = new_data.cast_column("audio", Audio(sampling_rate=16000))

        try:
            # Load the existing dataset from Hugging Face
            existing_dataset = load_dataset(huggingface_id)

            if len(new_data) >= 2:
                train_test_split = new_data.train_test_split(test_size=0.2)
                combined_train = concatenate_datasets([existing_dataset["train"], train_test_split["train"]])
                combined_test = concatenate_datasets([existing_dataset["test"], train_test_split["test"]])
            else:
                combined_train = concatenate_datasets([existing_dataset["train"], new_data])
                combined_test = existing_dataset["test"]
        except FileNotFoundError:
            # If the dataset doesn't exist on Hugging Face, create a new one
            if len(new_data) >= 2:
                train_test_split = new_data.train_test_split(test_size=0.2)
                combined_train = train_test_split["train"]
                combined_test = train_test_split["test"]
            else:
                combined_train = new_data
                combined_test = Dataset.from_dict({"audio": [], "transcription": []})

        # Create DatasetDict
        dataset_dict = DatasetDict({"train": combined_train, "test": combined_test})

        # Push updated dataset to Hugging Face
        dataset_dict.push_to_hub(huggingface_id)

        # Clear local storage after successful sync
        file.seek(0)
        json.dump({"audio": [], "transcription": []}, file)
        file.truncate()


scheduler.add_job(sync_data_with_huggingface, IntervalTrigger(minutes=10))

@app.route('/')
def index():
    return render_template('index.html')

@app.route("/random_transcription", methods=["GET"])
def random_transcription():
    transcription_data = get_random_transcription()
    if not transcription_data:
        return jsonify({"Error": "Nenhuma transcrição disponível"}), 404
    return jsonify(transcription_data)

@app.route("/upload_audio", methods=["POST"])
def upload_audio():
    audio_keys = [key for key in request.files.keys() if key.startswith('audios')]
    transcription_keys = [key for key in request.form.keys() if key.startswith('transcriptions')]

    if not audio_keys or not transcription_keys:
        return jsonify({"Error": "Áudios ou transcrições não foram enviados corretamente"}), 400

    data = {
        'audio': [],
        'transcription': []
    }

    for audio_key, transcription_key in zip(audio_keys, transcription_keys):
        audio_file = request.files[audio_key]
        transcription = request.form[transcription_key]

        audio_data = audio_file.read()
        audio = AudioSegment.from_file(io.BytesIO(audio_data))

        wav_io = io.BytesIO()
        audio.export(wav_io, format="wav")
        wav_io.seek(0)
        samples, sample_rate = sf.read(wav_io)

        data['audio'].append({"array": samples.tolist(), "sampling_rate": sample_rate})
        data['transcription'].append(transcription)

    # Append the data to the local storage
    with open(LOCAL_DATA_FILE, "r+") as file:
        local_data = json.load(file)
        local_data["audio"].extend(data["audio"])
        local_data["transcription"].extend(data["transcription"])
        file.seek(0)
        json.dump(local_data, file)
        file.truncate()

    return jsonify({"Mensagem": "Áudios recebidos e armazenados localmente"}), 200

@app.route("/save_audio/<int:transcription_id>", methods=["GET"])
def save_audio(transcription_id):
    response = invalidate_transcription(transcription_id)
    if response:
        return jsonify({"responseMessage": "Audio Salvo"}), 200
    return jsonify({"responseMessage": "Audio não foi Salvo"}), 400



@app.route("/add_transcription", methods=["POST"])
def add_transcription():
    transcription = request.form.get('transcription')
    if not transcription:
        return jsonify({"responseMessage": "Nenhuma transcrição foi enviada"}), 400

    success, message = add_transcription_on(transcription)
    if success:
        return jsonify({"responseMessage": message}), 200
    else:
        return jsonify({"responseMessage": message}), 400

@app.route("/list_transcriptions", methods=["GET"])
def list_transcriptions():
    transcriptions = list_valid_transcriptions()
    return jsonify(transcriptions)

@app.route("/delete_transcription/<int:transcription_id>", methods=["DELETE"])
def delete_transcription_route(transcription_id):
    success = delete_transcription(transcription_id)
    if success:
        return jsonify({"responseMessage": "Transcrição deletada com sucesso"}), 200
    else:
        return jsonify({"responseMessage": "Erro ao deletar transcrição"}), 400


@app.route('/add_transcription')
def add_transcription_page():
    return render_template('add_transcription.html')



if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
