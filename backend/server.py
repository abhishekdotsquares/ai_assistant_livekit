from flask import Flask, request, jsonify
from gtts import gTTS
import tempfile
import wave
from pydub import AudioSegment


app = Flask(__name__)

max_words = 150

@app.route('/get_audio_length', methods=['POST'])
def get_audio_length():

    # Get text from the POST request
    text = request.json.get('text')
    text = str(text)
    if not text:
        return jsonify({'error': 'No text provided'}), 400

    words = text.split(" ")

    if len(words) > 200:
        text = " ".join(words[:200])

    tts = gTTS(text=text, lang="en", slow=False)
    
    # Save to a temporary file
    with tempfile.NamedTemporaryFile(delete=True, suffix=".mp3") as temp_audio:
        tts.save(temp_audio.name)
        
        # Load the audio file and get duration
        audio = AudioSegment.from_file(temp_audio.name)
        duration_seconds = len(audio) / 1000  # Convert from milliseconds to seconds
    
    if duration_seconds > 60:
        text = " ".join(words[:max_words])

    return jsonify({'text': text, 'audio_length_seconds': duration_seconds})


def get_audio_duration(audio_io):
    # Calculate the length of the audio in seconds from the in-memory WAV buffer
    try:
        # AudioSegment handles WAV files natively
        with wave.open(audio_io, 'rb') as f:
            frames = f.getnframes()
            rate = f.getframerate()
            duration = frames / float(rate)
            return duration
    except Exception as e:
        return str(e)



if __name__ == '__main__':
    app.run(debug=True)
