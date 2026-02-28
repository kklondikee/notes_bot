import os
import json
import subprocess
import tempfile
from vosk import Model, KaldiRecognizer

MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models", "vosk-model-small-ru-0.22")

_model = None

def get_model():
    global _model
    if _model is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Модель Vosk не найдена по пути: {MODEL_PATH}\n"
                                   f"Скачайте модель с https://alphacephei.com/vosk/models\n"
                                   f"и распакуйте в папку models/")
        _model = Model(MODEL_PATH)
    return _model

async def voice_to_text(file_content: bytes) -> str:
    tmp_ogg_path = None
    tmp_wav_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.ogg') as tmp_ogg:
            tmp_ogg.write(file_content)
            tmp_ogg_path = tmp_ogg.name

        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_wav:
            tmp_wav_path = tmp_wav.name

        cmd = [
            'ffmpeg', '-i', tmp_ogg_path,
            '-acodec', 'pcm_s16le',
            '-ar', '16000',
            '-ac', '1',
            '-y',
            tmp_wav_path
        ]
        subprocess.run(cmd, check=True, capture_output=True)

        with open(tmp_wav_path, 'rb') as f:
            wav_data = f.read()

        model = get_model()
        rec = KaldiRecognizer(model, 16000)
        rec.AcceptWaveform(wav_data)
        result = json.loads(rec.FinalResult())
        text = result.get('text', '')

        return text

    except Exception as e:
        print(f"Ошибка в voice_to_text: {e}")
        return ""
    finally:
        for path in [tmp_ogg_path, tmp_wav_path]:
            if path and os.path.exists(path):
                try:
                    os.unlink(path)
                except:
                    pass