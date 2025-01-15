# ScriptAudio

ScriptAudio is a powerful toolkit for generating audio content using Google's Gemini Multimodal Live API. The application combines YouTube script generation and general content generation into a single, user-friendly interface with advanced audio quality controls.

## 🌟 Features

### Core Features
- Generate natural-sounding audio using Gemini's voices
- Support for all Gemini voices: Aoede, Charon, Fenrir, Kore, Puck
- Phoneme alignment validation for audio quality
- Variable replacement with AI-generated content
- Batch processing capabilities
- Progress tracking and detailed status updates
- Save audio in WAV format (24kHz, 16-bit PCM)
- Comprehensive metadata in labels.json
- User-friendly Gradio interface

### Content Generation
- YouTube Scripts:
  - Generate scripts with proper structure
  - Choose from various video categories and styles
  - Support for existing script library
  - Custom script input
  - Optimized for YouTube content delivery

- General Content:
  - Multiple content templates (Stories, Recipes, etc.)
  - Custom template support
  - Variable replacement system
  - Batch generation (1-50 items)
  - Length optimization (100-200 words)

## 🚀 Setup

1. Create and activate a virtual environment:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Unix/macOS
```

2. Install Python dependencies:
```bash
pip install google-genai opencv-python pyaudio pillow mss gradio phonemizer
```

3. Install espeak (required for audio quality validation):
- Windows: Download and install from [espeak website](http://espeak.sourceforge.net/download.html)
- Linux: `sudo apt-get install espeak`
- macOS: `brew install espeak`

4. Get your Gemini API key:
- Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
- Create a new API key
- Keep it secure for use in the application

Note: If espeak is not installed, the application will still work but audio quality validation will be disabled.

## 💻 Usage

Run the application:
```bash
python combined_audio_generator.py
```

The interface provides two main modes:

1. YouTube Scripts:
   - Select video category and style
   - Generate or input custom script
   - Convert to audio with quality validation

2. General Content:
   - Choose content template
   - Configure variables
   - Generate single or batch content
   - Convert to audio with quality checks

## 📁 Project Structure

```
ScriptAudio/
  ├── combined_audio_generator.py # Main application
  ├── README.md                  # Documentation
  ├── LICENSE                    # License file
  └── generated_audio/           # Output directory
      ├── labels.json            # Audio metadata
      └── voice-{name}-{num}.wav # Generated audio files
```

## 🎵 Audio Output

The labels.json file now includes quality metrics:
```json
{
  "samples": [
    {
      "audio_file": "voice-puck-001.wav",
      "text": "Content text here...",
      "duration": 32.5,
      "speaker_id": "puck",
      "timestamp": "2024-03-20T14:30:00Z",
      "alignment_score": 0.95,
      "alignment_passed": true
    }
  ]
}
```

## 🛠️ Advanced Features

### Quality Control
- Phoneme alignment validation (requires espeak)
- Minimum alignment threshold (0.8)
- Automatic quality checks
- Detailed quality metrics in metadata


### Variable Replacement

Both applications support dynamic variable replacement:
- Use [variable_name] syntax in your content
- Variables can be replaced manually or auto-generated
- AI-powered contextual replacements

Example:
```
Theme: [theme]
Setting: [setting]
Character: [character_name]
```

### Batch Processing
Efficient handling of multiple items:
- Parallel processing where possible
- Progress tracking
- Error handling and recovery
- Detailed processing reports

### Custom Templates
Create your own templates:
1. Select "Custom Template"
2. Define your structure
3. Add variables using [variable_name]
4. Set requirements and guidelines

### Voice Customization
Available voices with different characteristics:
- Aoede: Warm and engaging
- Charon: Deep and authoritative
- Fenrir: Energetic and dynamic
- Kore: Clear and professional
- Puck: Friendly and conversational

## 📊 Performance

Audio Generation:
- Format: 24kHz WAV, 16-bit PCM
- Typical Duration: 30-45 seconds per 100-200 words
- Processing Time: ~5-10 seconds per audio file

Content Generation:
- Word Count: 100-200 words per item
- Token Limit: ~512 tokens
- Generation Time: ~2-3 seconds per item

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📝 Notes

- Audio is generated in real-time using Gemini's latest models
- Each voice maintains its own sequential numbering
- Progress is shown during batch processing
- Labels are updated after each successful generation
- Error handling includes automatic retries
- System prompts ensure consistent output quality

## ⚠️ Limitations & API Limits

### API Limits
- Input Token Limit: 1,048,576 tokens (~1M)
- Output Token Limit: 8,192 tokens (~8K)
- Rate Limits:
  - 10 requests per minute (RPM)
  - 4 million tokens per minute (TPM)
  - 1,500 requests per day (RPD)

### Audio Configuration
- Input Audio: 16kHz, 16-bit PCM
- Output Audio: 24kHz, 16-bit PCM
- Mono Channel
- Batch Size: Up to 100 items
- Session Duration: 15 minutes max

### Content Limits
- Text Length: 10-200 words per item
- Alignment Score Threshold: 0.8
- Audio Duration: Optimized for 45 seconds or less

## 🎵 Audio Output

Generated audio files follow this naming convention:
```bash
voice-{voice_name}-{sequential_number}.wav
Example: voice-puck-001.wav
```

The labels.json file contains detailed metadata:
```json
{
  "samples": [
    {
      "audio_file": "voice-puck-001.wav",
      "text": "Content text here...",
      "duration": 32.5,
      "speaker_id": "puck",
      "timestamp": "2024-03-20T14:30:00Z",
      "alignment_score": 0.95,
      "alignment_passed": true
    }
  ]
}
```

## 🔒 Security

- API keys are handled securely
- No data is stored externally
- All processing is done locally
- Output files are saved in local directory

## 📚 Resources

- [Gemini API Documentation](https://ai.google.dev/docs)
- [Gradio Documentation](https://gradio.app/docs/)
- [Python Audio Processing](https://docs.python.org/3/library/wave.html)

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
