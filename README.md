# Audio Content Generator

Generate high-quality audio content using Gemini's Multimodal Live API. This tool allows you to create scripts, content, and convert them to natural-sounding audio using advanced AI voices.

## Features

- **YouTube Script Generation**
    - Multiple categories (Tech, Gaming, Cooking, etc.)
    - Various style options (energetic, calm, professional)
    - Batch processing up to 100 scripts
    - Separate script and audio generation

- **General Content Generation**
    - Blog posts, product reviews, tutorials, and more
    - Multiple niche options
    - Batch content creation
    - Flexible content-to-audio conversion

- **Advanced Audio Features**
    - Multiple AI voice options with different characteristics
    - Customizable tone presets
    - High-quality 24kHz audio output
    - Audio quality validation
    - Metadata tracking in labels.json

- **User Interface**
    - Intuitive Gradio-based interface
    - Separate tabs for YouTube and General content
    - Real-time status updates
    - Generated files list with refresh option
    - Progress tracking

## Installation

1. Clone the repository
2. Create and activate a virtual environment:
     ```bash
     python -m venv venv
     venv\Scripts\activate  # Windows
     source venv/bin/activate  # Linux/Mac
     ```
3. Install dependencies:
     ```bash
     pip install -r requirements.txt
     ```

## Usage

1. Activate the virtual environment if not already activated
2. Run the application:
     ```bash
     python run.py
     ```
3. Enter your Gemini API key in the interface
4. Choose your content generation mode:
     - **YouTube Scripts Tab:**
         - Select category and style
         - Choose number of scripts
         - Generate scripts only, audio only, or both
     - **General Content Tab:**
         - Select content type and niche
         - Set batch size
         - Generate content only, audio only, or both
5. Configure voice settings:
     - Select from available AI voices
     - Choose tone preset or create custom tone
     - Review voice characteristics

## Project Structure

- `src/`: Main package directory
    - `main.py`: Main application and Gradio interface
    - `audio_utils.py`: Audio generation and processing utilities
    - `content_generator.py`: Content generation functionality
    - `config.py`: Configuration constants and settings
    - `utils.py`: Utility functions and rate limiting
- `run.py`: Application entry point
- `requirements.txt`: Project dependencies
- `generated_audio/`: Output directory for generated audio files
    - `labels.json`: Metadata for generated audio files

## Generated Files

- Audio files are saved in the `generated_audio` directory
- Each audio file has associated metadata in `labels.json`:
    - Text content
    - Duration
    - Voice settings
    - Tone configuration
    - Quality metrics
    - Timestamp

## Requirements

- Python 3.8+
- Gemini API key
- espeak (optional, for audio quality validation)
- Internet connection for API access

## Voice Options

- **Aoede**: Warm and engaging - perfect for storytelling
- **Charon**: Deep and authoritative - ideal for educational content
- **Fenrir**: Energetic and dynamic - great for gaming content
- **Kore**: Clear and professional - suited for tutorials
- **Puck**: Friendly and conversational - best for vlogs

## Tone Presets

- **Default**: Natural and clear reading
- **Professional**: Authoritative with clear enunciation
- **Casual**: Natural pacing and conversational style
- **Custom**: User-defined tone instructions


