from flask import Flask, jsonify, render_template, request
from huggingface_hub import login
from datasets import Dataset, Audio, load_dataset, concatenate_datasets
from flask_cors import CORS
import io
import soundfile as sf
from pydub import AudioSegment
from database import *

app = Flask(__name__)
CORS(app)

load_dotenv()
huggingface_token = os.getenv("HUGGINGFACE_TOKEN")
huggingface_id = os.getenv("HUGGINGFACE_REPO_ID")

login(huggingface_token)

create_table_if_not_exists()

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
    transcription_id = request.form.get('transcription_id')  # Ajuste aqui

    if not audio_keys or not transcription_keys or not transcription_id:
        return jsonify({"Error": "Áudios ou transcrições não foram enviados corretamente"}), 400

    try:
        exists_dataset = load_dataset(huggingface_id, split="train")
        exists_transcriptions = set(exists_dataset['transcription'])
    except FileNotFoundError:
        exists_dataset = None
        exists_transcriptions = set()

    data = {
        'audio': [],
        'transcription': []
    }

    for audio_key, transcription_key in zip(audio_keys, transcription_keys):
        audio_file = request.files[audio_key]
        transcription = request.form[transcription_key]

        if transcription in exists_transcriptions:
            continue

        audio_data = audio_file.read()
        audio = AudioSegment.from_file(io.BytesIO(audio_data))

        wav_io = io.BytesIO()
        audio.export(wav_io, format="wav")
        wav_io.seek(0)
        samples, sample_rate = sf.read(wav_io)

        data['audio'].append({"array": samples, "sampling_rate": sample_rate})
        data['transcription'].append(transcription)

    if data['audio']:
        dataset = Dataset.from_dict(data)
        dataset = dataset.cast_column("audio", Audio(sampling_rate=16000))

        if exists_dataset:
            new_data = concatenate_datasets([exists_dataset, dataset])
        else:
            new_data = dataset

        new_data.push_to_hub(huggingface_id)

        # Invalidar a transcrição agora que o áudio foi salvo
        invalidate_transcription(transcription_id)

    return jsonify({"Mensagem": "Áudios recebidos e salvos com sucesso"}), 200

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


@app.route('/add_transcription')
def add_transcription_page():
    return render_template('add_transcription.html')


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
