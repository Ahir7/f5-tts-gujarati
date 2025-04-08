# F5-TTS Web Application

A modern web interface for Gujarati Text-to-Speech synthesis using the F5-TTS model.

![F5-TTS Web App](screenshots/preview.png)

## Features

- **Text-to-Speech Conversion**: Convert Gujarati text to natural-sounding speech
- **Advanced Generation Parameters**: Customize speech generation with adjustable parameters
- **Dark/Light Theme**: Toggle between dark and light mode for comfortable viewing
- **Audio History**: View, play, and download previously generated audio
- **Responsive Design**: Works on desktop and mobile devices
- **User Authentication**: Basic login system to protect the application

## Technologies Used

- **Backend**: Flask (Python)
- **Frontend**: HTML, CSS, JavaScript
- **TTS Engine**: F5-TTS model via Gradio API
- **Audio Processing**: Generated WAV files with customizable settings

## Setup & Installation

### Prerequisites

- Python 3.8+
- Gradio API running locally on port 7860
- The F5-TTS model files for Gujarati

### Installation

1. Clone the repository:
```bash
git clone https://github.com/Ahir7/f5-tts-web-app.git
cd f5-tts-web-app
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure the model paths in `app.py`:
Update the `LANGUAGES` dictionary with your local model paths.

### Running the Application

1. Start the Gradio API for the TTS model on port 7860.

2. Run the Flask application:
```bash
python app.py
```

3. Access the web interface at http://localhost:5000

## Usage

1. **Login**: Use the default credentials (admin/admin123) or update them in the app
2. **Enter Text**: Type or paste Gujarati text in the text area
3. **Adjust Parameters** (optional):
   - NFE Step: Adjust the number of function evaluations (default: 32)
   - Speed: Control speech speed (0.5-2.0)
   - Random Seed: Set for consistent output (or -1 for random)
   - Remove Silence: Toggle to trim silence
   - Use EMA: Toggle Exponential Moving Average usage
4. **Generate**: Click "Generate Speech" to process the text
5. **Listen & Download**: Play the audio in the browser or download it
6. **View History**: Access previously generated audio files

## Project Structure

- `app.py`: Main Flask application
- `templates/`: HTML templates
  - `index.html`: Main TTS interface
  - `login.html`: Login page
  - `history.html`: Audio history page
- `static/`: Static assets
  - `css/style.css`: Application styling
  - `js/script.js`: Client-side functionality
  - `audio/`: Generated audio files

## Customization

- **Adding Languages**: Add new language configurations to the `LANGUAGES` dictionary in `app.py`
- **Styling**: Modify the `static/css/style.css` file to change the appearance
- **Users**: Update the `users` dictionary in `app.py` to manage authentication

## License

[MIT License](LICENSE)

## Acknowledgements

- F5-TTS Model Team for the text-to-speech technology
- Contributors and maintainers of the original F5-TTS project

## Future Enhancements

- Database integration for user management
- Multiple language support
- Batch processing capabilities
- API key authentication
- Customizable voice profiles 