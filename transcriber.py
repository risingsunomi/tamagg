import whisper

class Transcriber:
    def __init__(self, model_name="base"):
        self.model = whisper.load_model(model_name)

    def transcribe(self, audio_file):
        print("Transcribing audio...")
        result = self.model.transcribe(audio_file)
        print("Transcription:", result["text"])
        return result["text"]