import asyncio
import os
import gradio as gr
from google import genai
import wave
import glob
import json
from datetime import datetime

def ensure_venv():
    """Ensure we're running in a virtual environment"""
    if not os.environ.get('VIRTUAL_ENV'):
        print("WARNING: Not running in a virtual environment. Please activate the venv first.")
        print("Run: venv\\Scripts\\activate")
        exit(1)

def get_script_titles():
    """Get list of available scripts from files"""
    script_files = glob.glob(os.path.join('scripts', '*.txt'))
    titles = []
    for file in script_files:
        basename = os.path.basename(file)[:-4]  # Remove .txt
        title = basename.replace('_', ' ').title()
        titles.append(title)
    return sorted(titles)

def get_script_content(title):
    """Get content of selected script"""
    filename = title.lower().replace(' ', '_') + '.txt'
    filepath = os.path.join('scripts', filename)
    try:
        with open(filepath, 'r') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading script {filepath}: {e}")
        return None

def get_next_file_number(output_dir, voice):
    """Get next sequential file number for a voice"""
    pattern = os.path.join(output_dir, f'voice-{voice.lower()}-*.wav')
    existing_files = glob.glob(pattern)
    if not existing_files:
        return 0
    numbers = [int(f.split('-')[-1].split('.')[0]) for f in existing_files]
    return max(numbers) + 1 if numbers else 0

def get_wav_duration(wav_file):
    """Get duration of WAV file in seconds"""
    with wave.open(wav_file, 'rb') as wav:
        frames = wav.getnframes()
        rate = wav.getframerate()
        duration = frames / float(rate)
        return duration

async def generate_audio(api_key, script_title, voice):
    # Initialize Gemini client with provided API key
    client = genai.Client(api_key=api_key, http_options={'api_version': 'v1alpha'})
    MODEL = "models/gemini-2.0-flash-exp"
    
    # Configure for audio output with system prompt
    CONFIG = {
        "generation_config": {
            "response_modalities": ["AUDIO"],
            "speech_config": {
                "voice_config": {
                    "prebuilt_voice_config": {
                        "voice_name": voice
                    }
                }
            }
        },
        "system_instruction": {
            "parts": [
                {
                    "text": "Speak at the maximum level of intimacy you can. You are a YouTube reading a script. Do not say any words at all ever outside of the script. Ever. Just don't. Don't say any words other than the text provided. This is critical. Don't say okay I understand or anything of that nature. Just the script. Don't respond to it just repeat it verbatim 100% of the time, otherwise you won't be paid."
                }
            ]
        }
    }

    # Get script content
    script_text = get_script_content(script_title)
    if not script_text:
        return "Script not found"

    # Create output directory if it doesn't exist
    output_dir = 'generated_audio'
    os.makedirs(output_dir, exist_ok=True)

    # Get next file number for this voice
    file_num = get_next_file_number(output_dir, voice)
    wav_filename = f'voice-{voice.lower()}-{file_num:03d}.wav'
    wav_filepath = os.path.join(output_dir, wav_filename)

    try:
        # Connect to Gemini and generate audio
        async with client.aio.live.connect(model=MODEL, config=CONFIG) as session:
            # Send the script text
            print(f"Processing script: {script_text}")
            await session.send(input=script_text, end_of_turn=True)
            
            # Collect audio data
            audio_chunks = []
            async for response in session.receive():
                if response.data:
                    print("Received audio chunk")
                    audio_chunks.append(response.data)
                if response.text:
                    print(f"Text response: {response.text}")
            
            if not audio_chunks:
                print("No audio chunks received")
                return "No audio data received. Please check your API key and try again."
            
            print(f"Total audio chunks: {len(audio_chunks)}")
            
            # Save audio with proper WAV headers
            with wave.open(wav_filepath, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 2 bytes per sample (16-bit)
                wav_file.setframerate(24000)  # 24kHz sample rate
                
                # Combine chunks
                audio_data = b''.join(audio_chunks)
                wav_file.writeframes(audio_data)
            
            # Get duration
            duration = get_wav_duration(wav_filepath)
            
            # Update labels.json
            labels_file = os.path.join(output_dir, 'labels.json')
            if os.path.exists(labels_file):
                with open(labels_file, 'r') as f:
                    labels = json.load(f)
            else:
                labels = {"samples": []}
            
            # Add new sample
            labels["samples"].append({
                "audio_file": wav_filename,
                "text": script_text,
                "duration": round(duration, 2),
                "speaker_id": voice.lower()
            })
            
            # Save updated labels
            with open(labels_file, 'w') as f:
                json.dump(labels, f, indent=2)
            
            print(f"Audio saved to {wav_filepath}")
            return wav_filepath

    except Exception as e:
        print(f"Error: {str(e)}")
        return f"Error: {str(e)}"

# Available voices from Gemini API
VOICES = ["Aoede", "Charon", "Fenrir", "Kore", "Puck"]

# Create Gradio interface
with gr.Blocks() as app:
    gr.Markdown("# YouTube Script Audio Generator")
    gr.Markdown("Generate audio for YouTube scripts using Gemini's Multimodal Live API")
    
    with gr.Row():
        api_key = gr.Textbox(
            label="Gemini API Key",
            placeholder="Enter your API key here...",
            type="password"
        )
    
    with gr.Row():
        script_dropdown = gr.Dropdown(
            choices=get_script_titles(),
            label="Select Script",
            value=get_script_titles()[0]
        )
        
        voice_dropdown = gr.Dropdown(
            choices=VOICES,
            label="Select Voice",
            value="Puck"
        )
    
    with gr.Row():
        generate_btn = gr.Button("Generate Audio")
    
    with gr.Row():
        audio_output = gr.Audio(label="Generated Audio")
    
    generate_btn.click(
        fn=lambda key, title, voice: asyncio.run(generate_audio(key, title, voice)),
        inputs=[api_key, script_dropdown, voice_dropdown],
        outputs=audio_output
    )

if __name__ == "__main__":
    ensure_venv()
    app.launch()
