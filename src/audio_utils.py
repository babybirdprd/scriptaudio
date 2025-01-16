import asyncio
import base64
import contextlib
import json
import logging
import numpy as np

import os
import glob
import wave

import websockets
from datetime import datetime
from .config import *

@contextlib.contextmanager
def wave_file(filename, channels=WAVE_CHANNELS, rate=WAVE_RATE, sample_width=WAVE_SAMPLE_WIDTH):
	"""Context manager for creating and managing wave files."""
	try:
		with wave.open(filename, "wb") as wf:
			wf.setnchannels(channels)
			wf.setsampwidth(sample_width)
			wf.setframerate(rate)
			yield wf
	except wave.Error as e:
		logging.error(f"Error opening wave file '{filename}': {e}")
		raise

async def audio_playback_task(file_name, stop_event):
	"""Plays audio using pygame until stopped."""
	try:
		pygame.mixer.music.load(file_name)
		pygame.mixer.music.play()
		while pygame.mixer.music.get_busy() and not stop_event.is_set():
			await asyncio.sleep(0.1)
	except pygame.error as e:
		logging.error(f"Pygame error during playback: {e}")
	except Exception as e:
		logging.error(f"Unexpected error during playback: {e}")

def get_next_file_number(output_dir, voice):
	"""Get next available file number for audio output"""
	pattern = os.path.join(output_dir, f'voice-{voice.lower()}-*.wav')
	existing_files = glob.glob(pattern)
	if not existing_files:
		return 0
	numbers = [int(f.split('-')[-1].split('.')[0]) for f in existing_files]
	return max(numbers) + 1 if numbers else 0

def update_labels_file(wav_filepath: str, wav_filename: str, text: str, voice: str, audio_array: np.ndarray) -> None:
	"""Update the labels.json file with new audio metadata"""
	try:
		output_dir = os.path.dirname(wav_filepath)
		labels_file = os.path.join(output_dir, 'labels.json')
		
		if os.path.exists(labels_file):
			with open(labels_file, 'r', encoding='utf-8') as f:
				labels = json.load(f)
		else:
			labels = {"samples": []}

		with wave.open(wav_filepath, 'rb') as wav:
			frames = wav.getnframes()
			rate = wav.getframerate()
			duration = frames / float(rate)

		sample_data = {
			"audio_file": wav_filename,
			"text": text,
			"duration": round(duration, 2),
			"speaker_id": voice.lower(),
			"timestamp": datetime.now().isoformat(),
			"sample_rate": WAVE_RATE,
			"channels": WAVE_CHANNELS,
			"file_size": os.path.getsize(wav_filepath)
		}

		labels["samples"].append(sample_data)

		with open(labels_file, 'w', encoding='utf-8') as f:
			json.dump(labels, f, indent=2, ensure_ascii=False)

	except Exception as e:
		logging.error(f"Error updating labels file: {str(e)}")
		raise

async def generate_audio(api_key, text, voice, tone_preset="Default", custom_tone="", progress=None):
	"""Generate audio from text using Gemini API"""
	if not api_key:
		return None, "API key is required"

	URI = f'wss://{HOST}/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContent?key={api_key}'
	
	output_dir = 'generated_audio'
	os.makedirs(output_dir, exist_ok=True)

	file_num = get_next_file_number(output_dir, voice)
	wav_filename = f'voice-{voice.lower()}-{file_num:03d}.wav'
	wav_filepath = os.path.join(output_dir, wav_filename)

	try:
		if progress:
			progress(0.1, desc=STATUS_MESSAGES["connecting"])
			
		async with websockets.connect(URI) as ws:
			config = {
				"response_modalities": ["AUDIO"],
				"speech_config": {
					"voice_config": {
						"prebuilt_voice_config": {
							"voice_name": voice
						}
					}
				}
			}

			await ws.send(json.dumps({
				"setup": {
					"model": MODEL,
					"generation_config": config
				}
			}))

			raw_response = await ws.recv(decode=False)
			setup_response = json.loads(raw_response.decode("ascii"))
			
			if progress:
				progress(0.2, desc=STATUS_MESSAGES["connecting"])

			msg = {
				"clientContent": {
					"turns": [{
						"role": "user", 
						"parts": [{
							"text": f"INSTRUCTION: Read the following text verbatim, word for word, without responding to it as if in conversation. Do not add any commentary, responses, or modifications. Simply read exactly what is provided:\n\n{text}"
						}]
					}],
					"turnComplete": True
				}
			}
			await ws.send(json.dumps(msg))

			responses = []
			async for raw_response in ws:
				try:
					response = json.loads(raw_response.decode())
					server_content = response.get("serverContent")
					if server_content is None:
						break

					model_turn = server_content.get("modelTurn")
					if model_turn:
						parts = model_turn.get("parts")
						if parts:
							for part in parts:
								if "inlineData" in part and "data" in part["inlineData"]:
									pcm_data = base64.b64decode(part["inlineData"]["data"])
									responses.append(np.frombuffer(pcm_data, dtype=np.int16))
									if progress:
										progress(0.5, desc=STATUS_MESSAGES["generating"])

					if server_content.get("turnComplete"):
						break
				except json.JSONDecodeError as e:
					logging.error(f"JSON decode error: {str(e)}")
					continue
				except Exception as e:
					logging.error(f"Error processing response: {str(e)}")
					continue

			if responses:
				if progress:
					progress(0.9, desc=STATUS_MESSAGES["saving"])
					
				audio_array = np.concatenate(responses)
				with wave_file(wav_filepath) as wf:
					wf.writeframes(audio_array.tobytes())
				
				update_labels_file(wav_filepath, wav_filename, text, voice, audio_array)
				
				if progress:

					progress(1.0, desc=STATUS_MESSAGES["complete"])
					
				return wav_filepath, f"Audio generated successfully: {wav_filename}"
			else:
				return None, STATUS_MESSAGES["error_no_audio"]

	except websockets.exceptions.WebSocketException as e:
		logging.error(f"WebSocket error: {str(e)}")
		return None, f"WebSocket error: {str(e)}"
	except Exception as e:
		logging.error(f"Error generating audio: {str(e)}")
		return None, f"Error generating audio: {str(e)}"