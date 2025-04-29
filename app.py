# app.py - Updated with the working direct approach
from flask import Flask, request, jsonify, send_file, session, render_template, redirect, url_for
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from gradio_client import Client, handle_file
import os
import tempfile
import uuid
import traceback
import datetime
import glob
from flask_pymongo import PyMongo
from bson.objectid import ObjectId

# Create the Flask application instance
app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = 'your_secret_key'  # Change this to a random string
CORS(app)

# MongoDB Configuration with proper authentication and error handling
try:
    # Use the credentials you set in docker-compose.yml
    app.config["MONGO_URI"] = "mongodb://admin:password@localhost:27017/tts_app?authSource=admin"
    mongo = PyMongo(app)
    
    # Test the connection
    mongo.db.command('ping')
    print("MongoDB connection successful")
    
    # Initialize the database
    def init_db():
        try:
            # Create index on username for faster lookups
            mongo.db.users.create_index("username", unique=True)
            
            # Check if users collection exists and has at least one user
            if mongo.db.users.count_documents({}) == 0:
                # Add default admin user
                mongo.db.users.insert_one({
                    'username': 'admin',
                    'password': generate_password_hash('admin123'),
                    'name': 'Admin User'
                })
                print("Initialized database with admin user")
        except Exception as e:
            print(f"Database initialization error: {e}")
    
    # Initialize the database
    init_db()
    
except Exception as e:
    print(f"MongoDB connection error: {e}")
    print("Make sure your MongoDB Docker container is running with the correct credentials")

# Register routes here...

# TTS API configuration
TTS_API_URL = "http://127.0.0.1:7860/"
client = Client(TTS_API_URL)

# Temporary directory for storing generated audio files
TEMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'audio')
os.makedirs(TEMP_DIR, exist_ok=True)

# Supported languages and their configurations
LANGUAGES = {
    'gujarati': {
        'project': 'guj_tts_by_harsh_char',
        'checkpoint': r"C:\Users\harsh\Desktop\TTS_by_Harsh\F5-TTS-kaggle_small\F5-TTS-kaggle_small\src\f5_tts\..\..\ckpts\guj_tts_by_harsh\model_24000.pt",
        'model': 'F5TTS_Base',
        'ref_text': "મિરપુરમાં ડે નાઇટ મેચમાં રાત્રે ઝાકળને કારણે, બોલરોને બોલની ગ્રીપ પકડતા તકલીફ પડતી હોય છે.",
        'ref_audio': r"C:\Users\harsh\AppData\Local\Temp\gradio\6abf6bd2c9fc8e22d2757791c3afd2971cb1df63d89c749b24f38be4d2f51e5b\train_gujaratimale_00643.wav"
    }
    # Add more languages as needed
}

# Function to convert MongoDB document to JSON-serializable format
def mongo_doc_to_dict(doc):
    if doc is None:
        return None
    doc_dict = dict(doc)
    # Convert ObjectId to string
    if '_id' in doc_dict:
        doc_dict['_id'] = str(doc_dict['_id'])
    return doc_dict

# Function to load or create audio metadata
def load_audio_metadata(username=None):
    query = {}
    if username:
        query['user'] = username
    return [mongo_doc_to_dict(doc) for doc in mongo.db.audio_metadata.find(query)]

# Function to save audio metadata
def save_audio_metadata(audio_data):
    return mongo.db.audio_metadata.insert_one(audio_data)

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
        
        user = mongo.db.users.find_one({"username": username})
        
        if user and check_password_hash(user['password'], password):
            session['username'] = username
            session['name'] = user['name']
            return redirect(url_for('index'))
        
        return render_template('login.html', error='Invalid username or password')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('name', None)
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        name = request.form.get('name')
        
        # Check if username already exists
        existing_user = mongo.db.users.find_one({"username": username})
        if existing_user:
            return render_template('register.html', error='Username already exists')
            
        hashed_password = generate_password_hash(password)
        
        mongo.db.users.insert_one({
            "username": username,
            "password": hashed_password,
            "name": name
        })
        
        return redirect(url_for('login'))
    
    return render_template('register.html')

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
        
        # Save metadata about this audio file to MongoDB
        metadata = {
            'filename': filename,
            'text': text,
            'language': language,
            'timestamp': datetime.datetime.now(),
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
    
    # Load metadata for current user from MongoDB
    audio_files = load_audio_metadata(session['username'])
    
    # Filter out files that don't exist anymore
    existing_audio_files = []
    for audio in audio_files:
        if 'filename' in audio and os.path.exists(os.path.join(TEMP_DIR, audio['filename'])):
            existing_audio_files.append(audio)
    
    # Sort by timestamp, newest first
    sorted_audio = sorted(
        existing_audio_files,
        key=lambda x: x.get('timestamp', datetime.datetime.min),
        reverse=True
    )
    
    return render_template('history.html', audio_files=sorted_audio)

# Add an admin panel route
@app.route('/admin/users')
def admin_users():
    if 'username' not in session or session['username'] != 'admin':
        return redirect(url_for('login'))
    
    users = list(mongo.db.users.find())
    # Convert ObjectId to string for JSON serialization
    for user in users:
        user['_id'] = str(user['_id'])
    
    return render_template('admin_users.html', users=users)

# Add a user creation route for admin
@app.route('/admin/users/create', methods=['GET', 'POST'])
def admin_create_user():
    if 'username' not in session or session['username'] != 'admin':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        name = request.form.get('name')
        
        # Check if username already exists
        existing_user = mongo.db.users.find_one({"username": username})
        if existing_user:
            return render_template('admin_create_user.html', error='Username already exists')
            
        hashed_password = generate_password_hash(password)
        
        mongo.db.users.insert_one({
            "username": username,
            "password": hashed_password,
            "name": name
        })
        
        return redirect(url_for('admin_users'))
    
    return render_template('admin_create_user.html')

@app.route('/debug/mongo')
def debug_mongo():
    try:
        # Check MongoDB connection
        mongo.db.command('ping')
        
        # Get user count
        user_count = mongo.db.users.count_documents({})
        
        # Get a list of users (only names for security)
        users = [{"username": user["username"], "name": user["name"]} 
                for user in mongo.db.users.find()]
        
        return jsonify({
            "status": "MongoDB connected",
            "user_count": user_count,
            "users": users
        })
    except Exception as e:
        return jsonify({
            "status": "MongoDB error",
            "error": str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)