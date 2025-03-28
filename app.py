# app.py - Updated with the working direct approach
from flask import Flask, request, jsonify, send_file, session, render_template, redirect, url_for
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from gradio_client import Client, handle_file
import os
import tempfile
import uuid
import json
import traceback
import datetime
import glob

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = 'your_secret_key'  # Change this to a random string
CORS(app)

# Mock user database (replace with a real database in production)
users = {
    'admin': {
        'password': generate_password_hash('admin123'),
        'name': 'Admin User'
    }
}

# TTS API configuration
TTS_API_URL = "http://127.0.0.1:7860/"
client = Client(TTS_API_URL)

# Temporary directory for storing generated audio files
TEMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'audio')
os.makedirs(TEMP_DIR, exist_ok=True)

# File to store metadata about generated audio
AUDIO_METADATA_FILE = os.path.join(TEMP_DIR, 'metadata.json')

# Supported languages and their configurations
LANGUAGES = {
    'gujarati': {
        'project': 'guj_tts_by_harsh_char',
        'checkpoint': r"C:\Users\harsh\Desktop\TTS_by_Harsh\F5-TTS-kaggle_small\F5-TTS-kaggle_small\src\f5_tts\..\..\ckpts\guj_tts_by_harsh\model_24000.pt",
        'model': 'F5TTS_Base',
        'ref_text': "કૂવાની આસપાસ બંગડીયોનો ખણખણાટ રૂમઝૂમતો વર્તાય છે.",
        'ref_audio': r"C:\Users\harsh\AppData\Local\Temp\gradio\d9968d57c887c29feba3cc8814945fc25244dc6a07a44283084d1ffda8a2ff4c\train_gujaratimale_00813.wav"
    }
    # Add more languages as needed
}

# Function to load or create audio metadata
def load_audio_metadata():
    if os.path.exists(AUDIO_METADATA_FILE):
        with open(AUDIO_METADATA_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

# Function to save audio metadata
def save_audio_metadata(metadata):
    with open(AUDIO_METADATA_FILE, 'w') as f:
        json.dump(metadata, f, indent=2)

@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('index.html', languages=LANGUAGES.keys())

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username in users and check_password_hash(users[username]['password'], password):
            session['username'] = username
            session['name'] = users[username]['name']
            return redirect(url_for('index'))
        
        return render_template('login.html', error='Invalid username or password')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('name', None)
    return redirect(url_for('login'))

@app.route('/generate-speech', methods=['POST'])
def generate_speech():
    if 'username' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    data = request.json
    text = data.get('text', '')
    language = data.get('language', 'gujarati')
    
    if not text:
        return jsonify({'error': 'Text is required'}), 400
    
    if language not in LANGUAGES:
        return jsonify({'error': f'Language {language} is not supported'}), 400
    
    try:
        # Generate a unique filename
        filename = f"{uuid.uuid4()}.wav"
        output_path = os.path.join(TEMP_DIR, filename)
        
        # Get language configuration
        lang_config = LANGUAGES[language]
        
        print(f"Generating speech for text: {text[:30]}...")
        
        # Create a new client instance for each request to avoid any potential issues
        direct_client = Client("http://127.0.0.1:7860/")
        
        # Use the working approach from the test script
        result = direct_client.predict(
            project=lang_config['project'],
            file_checkpoint=lang_config['checkpoint'],
            exp_name=lang_config['model'],
            ref_text=lang_config['ref_text'],
            # Use handle_file instead of file (which is deprecated)
            ref_audio=handle_file(lang_config['ref_audio']),
            gen_text=text,  # Use the user's input text
            nfe_step=data.get('nfe_step', 32),
            use_ema=data.get('use_ema', False),
            speed=data.get('speed', 1),
            seed=data.get('seed', 42),
            remove_silence=data.get('remove_silence', False),
            api_name="/infer"
        )
        
        print(f"API result: {result}")
        
        # The result is a tuple with audio file as the first element
        audio_file = result[0] if isinstance(result, tuple) else result
        
        print(f"Generated audio file: {audio_file}")
        
        # Copy the audio file to our static directory
        with open(audio_file, 'rb') as src_file:
            with open(output_path, 'wb') as dst_file:
                dst_file.write(src_file.read())
        
        # Save metadata about this audio file
        metadata = load_audio_metadata()
        metadata[filename] = {
            'text': text,
            'language': language,
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'user': session['username'],
            'parameters': {
                'nfe_step': data.get('nfe_step', 32),
                'use_ema': data.get('use_ema', False),
                'speed': data.get('speed', 1),
                'seed': data.get('seed', 42),
                'remove_silence': data.get('remove_silence', False)
            }
        }
        save_audio_metadata(metadata)
        
        return jsonify({
            'success': True,
            'audio_url': f'/static/audio/{filename}',
            'download_url': url_for('download_file', filename=filename)
        })
    
    except Exception as e:
        print(f"Error generating speech: {e}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    file_path = os.path.join(TEMP_DIR, filename)
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
    
    return send_file(file_path, as_attachment=True)

@app.route('/history')
def history():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Load metadata for all audio files
    metadata = load_audio_metadata()
    
    # Filter audio files for current user
    user_audio = {}
    for filename, data in metadata.items():
        if data.get('user') == session['username']:
            # Check if the file still exists
            if os.path.exists(os.path.join(TEMP_DIR, filename)):
                user_audio[filename] = data
    
    # Sort by timestamp, newest first
    sorted_audio = sorted(
        [{'filename': k, **v} for k, v in user_audio.items()],
        key=lambda x: x['timestamp'],
        reverse=True
    )
    
    return render_template('history.html', audio_files=sorted_audio)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)