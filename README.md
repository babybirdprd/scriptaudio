# Audio Content Generator

A powerful application for generating high-quality audio content using Google's Gemini Multimodal Live API. Generate YouTube scripts, blog posts, and other content with customizable voices and tones.

## 🌟 Features

### Audio Generation
- Text-to-speech using Gemini's Multimodal Live API
- Multiple voice options with distinct characteristics:
  - Aoede: Warm and engaging - perfect for storytelling
  - Charon: Deep and authoritative - ideal for educational content
  - Fenrir: Energetic and dynamic - great for gaming content
  - Kore: Clear and professional - suited for tutorials
  - Puck: Friendly and conversational - best for vlogs
- Customizable voice tones:
  - Default: Natural and clear reading
  - Professional: Authoritative with clear enunciation
  - Casual: Natural and conversational
  - Custom: Define your own tone instructions
- High-quality audio output (24kHz, 16-bit PCM)
- Real-time audio playback with pygame
- Audio quality validation with phoneme alignment

### Content Generation
- YouTube Scripts:
  - Multiple categories (Tech, Gaming, Cooking, etc.)
  - Various styles (energetic, calm, humorous, etc.)
  - Structured output with hook and call-to-action
- General Content:
  - Blog posts, product reviews, tutorials
  - Multiple niches and topics
  - Natural, conversational style
- Batch processing support
- Word count optimization (100-200 words)

## 🚀 Setup

1. Create and activate a virtual environment:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Unix/macOS
```

2. Install dependencies:
```bash
pip install google-genai gradio phonemizer wave numpy pygame websockets
```

3. Optional: Install espeak for audio quality validation:
- Windows: Download from [espeak website](http://espeak.sourceforge.net/download.html)
- Linux: `sudo apt-get install espeak`
- macOS: `brew install espeak`

4. Get your Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)

## 💻 Usage

1. Run the application:
```bash
python combined_audio_generator.py
```

2. Enter your Gemini API key
3. Choose content type (YouTube Scripts or General Content)
4. Configure settings:
   - Select voice
   - Choose tone preset or enter custom tone
   - Set content parameters
5. Generate content and audio
6. Listen to generated audio with real-time playback

## 📊 Technical Details

### API Limits
- Requests: 10 per minute
- Tokens: 4M per minute
- Daily limit: 1,500 requests

### Audio Configuration
- Input sample rate: 16kHz
- Output sample rate: 24kHz
- Format: WAV, mono, 16-bit PCM
- Session duration: 15 minutes max
- Real-time playback using pygame

### Content Limits
- Word count: 10-200 words
- Alignment threshold: 0.8
- Batch size: Up to 100 items

## 📁 Output

Generated files are saved in the `generated_audio` directory:
- Audio files: `voice-{name}-{number}.wav`
- Metadata: `labels.json` with quality metrics and playback info

## ⚠️ Notes

- Audio quality validation requires espeak
- All voices use strict text-to-speech mode
- Tone presets modify speaking style while maintaining verbatim reading
- Custom tones should follow the format: "TONE: [instruction]"
- Real-time playback requires pygame installation

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

