// static/js/script.js - Updated to include generation parameters
document.addEventListener('DOMContentLoaded', function() {
    const generateBtn = document.getElementById('generate-btn');
    const textInput = document.getElementById('text');
    const languageSelect = document.getElementById('language');
    const nfeStepInput = document.getElementById('nfe-step');
    const speedInput = document.getElementById('speed');
    const seedInput = document.getElementById('seed');
    const removeSilenceCheckbox = document.getElementById('remove-silence');
    const useEmaCheckbox = document.getElementById('use-ema');
    const loadingElement = document.getElementById('loading');
    const resultSection = document.getElementById('result');
    const audioPlayer = document.getElementById('audio-player');
    const downloadLink = document.getElementById('download-link');
    
    generateBtn.addEventListener('click', async function() {
        const text = textInput.value.trim();
        const language = languageSelect.value;
        const nfeStep = parseInt(nfeStepInput.value, 10);
        const speed = parseFloat(speedInput.value);
        const seed = parseInt(seedInput.value, 10);
        const removeSilence = removeSilenceCheckbox.checked;
        const useEma = useEmaCheckbox.checked;
        
        if (!text) {
            alert('Please enter text to convert to speech.');
            return;
        }
        
        // Show loading indicator
        loadingElement.style.display = 'block';
        resultSection.style.display = 'none';
        generateBtn.disabled = true;
        
        try {
            const response = await fetch('/generate-speech', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    text: text,
                    language: language,
                    nfe_step: nfeStep,
                    speed: speed,
                    seed: seed,
                    remove_silence: removeSilence,
                    use_ema: useEma
                })
            });
            
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            // Update audio player and download link
            audioPlayer.src = data.audio_url + '?t=' + new Date().getTime(); // Add timestamp to prevent caching
            downloadLink.href = data.download_url;
            
            // Show result section
            resultSection.style.display = 'block';
        } catch (error) {
            alert('Error generating speech: ' + error.message);
        } finally {
            // Hide loading indicator
            loadingElement.style.display = 'none';
            generateBtn.disabled = false;
        }
    });
});
