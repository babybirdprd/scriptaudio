import asyncio
import os
import glob
import json
import wave
from google import genai

async def generate_audio_for_script(session, script_text, voice, file_num, output_dir):
    """Generate audio for a single script"""
    wav_filename = f'voice-{voice.lower()}-{file_num:03d}.wav'
    wav_filepath = os.path.join(output_dir, wav_filename)
    
    print(f"\nProcessing script ({file_num}): {script_text[:100]}...")
    
    try:
        # Send the script text
        await session.send(input=script_text, end_of_turn=True)
        
        # Collect audio data
        audio_chunks = []
        async for response in session.receive():
            if response.data:
                print(".", end="", flush=True)  # Progress indicator
                audio_chunks.append(response.data)
            if response.text:
                print(f"\nText response: {response.text}")
        
        if not audio_chunks:
            print("\nNo audio chunks received")
            return None
        
        print(f"\nTotal chunks: {len(audio_chunks)}")
        
        # Save audio with proper WAV headers
        with wave.open(wav_filepath, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 2 bytes per sample (16-bit)
            wav_file.setframerate(24000)  # 24kHz sample rate
            
            # Combine chunks
            audio_data = b''.join(audio_chunks)
            wav_file.writeframes(audio_data)
        
        # Get duration
        with wave.open(wav_filepath, 'rb') as wav:
            frames = wav.getnframes()
            rate = wav.getframerate()
            duration = frames / float(rate)
        
        print(f"Saved: {wav_filename}")
        
        return {
            "audio_file": wav_filename,
            "text": script_text,
            "duration": round(duration, 2),
            "speaker_id": voice.lower()
        }
        
    except Exception as e:
        print(f"\nError generating audio: {str(e)}")
        return None

async def batch_generate(api_key, voice):
    # Initialize Gemini client
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
    
    # Create output directory
    output_dir = 'generated_audio'
    os.makedirs(output_dir, exist_ok=True)
    
    # Load scripts - prefer processed scripts if available
    processed_dir = 'processed_scripts'
    original_dir = 'scripts'
    
    if os.path.exists(processed_dir) and glob.glob(os.path.join(processed_dir, '*.txt')):
        script_dir = processed_dir
        print("Using processed scripts from processed_scripts/")
    else:
        script_dir = original_dir
        print("Using original scripts from scripts/")
    
    script_files = sorted(glob.glob(os.path.join(script_dir, '*.txt')))
    total_scripts = len(script_files)
    print(f"Found {total_scripts} scripts to process")
    
    # Initialize or load labels.json
    labels_file = os.path.join(output_dir, 'labels.json')
    if os.path.exists(labels_file):
        with open(labels_file, 'r') as f:
            labels = json.load(f)
    else:
        labels = {"samples": []}
    
    # Process each script
    async with client.aio.live.connect(model=MODEL, config=CONFIG) as session:
        for i, script_file in enumerate(script_files):
            with open(script_file, 'r') as f:
                script_text = f.read()
            
            result = await generate_audio_for_script(
                session=session,
                script_text=script_text,
                voice=voice,
                file_num=i,
                output_dir=output_dir
            )
            
            if result:
                labels["samples"].append(result)
                # Save labels after each successful generation
                with open(labels_file, 'w') as f:
                    json.dump(labels, f, indent=2)
            
            print(f"Progress: {i+1}/{total_scripts}")
    
    print("\nBatch processing complete!")
    print(f"Successfully processed: {len(labels['samples'])}/{total_scripts}")
    print(f"Output directory: {output_dir}")
    print(f"Labels file: {labels_file}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Batch generate audio for all scripts')
    parser.add_argument('--api-key', required=True, help='Gemini API Key')
    parser.add_argument('--voice', default='Puck', 
                      choices=["Aoede", "Charon", "Fenrir", "Kore", "Puck"],
                      help='Voice to use for all scripts (default: Puck)')
    
    args = parser.parse_args()
    asyncio.run(batch_generate(args.api_key, args.voice))
