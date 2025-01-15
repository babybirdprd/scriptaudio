# YouTube Script Audio Generator

This project uses Google's Gemini Multimodal Live API to generate audio for YouTube scripts with natural-sounding voices. It includes variable replacement for script templates and batch processing capabilities.

## Features

- Generate audio from YouTube scripts using Gemini's voices
- Replace template variables (e.g., [artist_name], [animal]) with AI-generated content
- Batch process multiple scripts
- Save audio in WAV format with proper metadata
- Support for all Gemini voices: Aoede, Charon, Fenrir, Kore, Puck

## Setup

1. Create and activate a virtual environment:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Unix/macOS
```

2. Install dependencies:
```bash
pip install google-genai opencv-python pyaudio pillow mss gradio
```

3. Set up your Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)

## Usage

### 1. Preprocess Scripts (Optional)

If your scripts contain template variables like [artist_name] or [animal], first run the preprocessing script:

```bash
python preprocess_scripts.py --api-key YOUR_API_KEY
```

This will:
- Process all scripts in the `scripts/` directory
- Replace variables with AI-generated content
- Save processed scripts to `processed_scripts/`
- Generate a processing report

### 2. Generate Audio

#### Option 1: Batch Processing (Recommended)
Process all scripts at once with a single voice:

```bash
python batch_generate.py --api-key YOUR_API_KEY --voice Puck
```

This will:
- Process all scripts sequentially
- Save WAV files as voice-puck-000.wav, voice-puck-001.wav, etc.
- Create labels.json with metadata
- Save everything in generated_audio/

#### Option 2: Interactive Web Interface
For individual script processing:

```bash
python app.py
```

Then:
1. Open http://localhost:7860 in your browser
2. Enter your API key
3. Select a script and voice
4. Click Generate Audio

## Output Format

The generated files follow this structure:
```
generated_audio/
  ├── labels.json
  ├── voice-puck-000.wav
  ├── voice-puck-001.wav
  ├── voice-puck-002.wav
  └── ...
```

The labels.json file contains metadata:
```json
{
  "samples": [
    {
      "audio_file": "voice-puck-000.wav",
      "text": "Script content here...",
      "duration": 2.5,
      "speaker_id": "puck"
    },
    ...
  ]
}
```

## Scripts

- `app.py`: Web interface for individual script processing
- `batch_generate.py`: Process all scripts with one voice
- `preprocess_scripts.py`: Replace template variables
- `parse_scripts.py`: Split JSON scripts into individual files
- `generate_scripts.py`: Generate new YouTube scripts using Gemini

### Script Generation

You can generate new YouTube scripts using the script generator:

```bash
python generate_scripts.py --api-key YOUR_API_KEY --num-scripts 100 --output scripts.json
```

This will:
- Generate the specified number of scripts using Gemini's latest model (gemini-1.5-pro-latest)
- Use structured output with TypedDict schema to ensure consistent JSON format
- Save scripts in the exact format required by script.json
- Automatically create numbered files (e.g., scripts.json, scripts_1.json) to prevent overwrites
- Provide detailed progress and error information during generation

Options:
- `--api-key`: Your Gemini API key (required)
- `--num-scripts`: Number of scripts to generate (default: 100)
- `--output`: Output JSON file (default: generated_scripts.json)

The generated scripts will be in various categories like Tech Review, Gaming, Cooking, etc., and each script will:
- Have an engaging opening hook
- Use natural, conversational YouTube style
- Include audience engagement phrases
- Be between 100-200 words
- End with a clear call to action
- Match the specified style (e.g., energetic, calm, humorous)

Output Format:
```json
{
  "response": "[{\"title\": \"Script Title\", \"script\": \"Script Content\"}, ...]"
}
```

Features:
- Robust error handling with retries for failed generations
- JSON validation to ensure proper structure
- Progress tracking with script titles
- Automatic file numbering to prevent data loss

## Notes

- Audio is generated in 24kHz WAV format with 16-bit PCM encoding
- Each voice maintains its own sequential numbering
- The system prompt ensures YouTube-style delivery
- Progress is shown during batch processing
- Labels are updated after each successful generation
