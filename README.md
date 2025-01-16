# Audio Content Generator

Generate high-quality audio content using Gemini's Multimodal Live API.

## Features

- YouTube script generation with multiple categories and styles
- General content generation with customizable templates
- Multiple voice options with different characteristics
- Batch processing support
- Audio quality validation
- Variable replacement

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
4. Choose between YouTube Scripts or General Content generation
5. Configure your content settings and voice preferences
6. Generate audio content

## Project Structure

- `src/`: Main package directory
  - `main.py`: Main application and Gradio interface
  - `audio_utils.py`: Audio generation and processing utilities
  - `content_generator.py`: Content generation functionality
  - `config.py`: Configuration constants and settings
  - `utils.py`: Utility functions and rate limiting
- `run.py`: Application entry point
- `requirements.txt`: Project dependencies

## Requirements

- Python 3.8+
- Gemini API key
- espeak (optional, for audio quality validation)


