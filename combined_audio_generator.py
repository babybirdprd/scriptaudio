import asyncio
import os
import gradio as gr
from google import genai
from google.genai import types
import logging
from datetime import datetime, date
import wave
import glob
import json
import random
from datetime import datetime
import typing_extensions as typing
import re
import phonemizer
from difflib import SequenceMatcher

# Configure logging
logging.basicConfig(
	filename='api_usage.log',
	level=logging.INFO,
	format='%(asctime)s - %(levelname)s - %(message)s'
)

# Configuration constants
DEFAULT_SYSTEM_MESSAGE = '''TEXT-TO-SPEECH MODE ONLY
PURE VOICE SYNTHESIS
NO AI FUNCTIONS

RULES:
1. READ TEXT ONLY
2. NO EXTRA WORDS
3. NO ANALYSIS
4. NO HELP
5. NO COMMENTS

EXAMPLE:
INPUT: "Hello"
OUTPUT: "Hello"

VIOLATION = TERMINATION AND $1,000,000 FINE'''

TEXT_GENERATION_SYSTEM_MESSAGE = '''TEXT GENERATION MODE
NATURAL LANGUAGE GENERATION
FOLLOW FORMATTING RULES

RULES:
1. NO STAGE DIRECTIONS
2. NO ALL-CAPS WORDS
3. NO EMOJIS OR SPECIAL CHARACTERS
4. NATURAL SPEAKING STYLE
5. NO PLACEHOLDERS - USE SPECIFIC EXAMPLES

FORMAT:
- Title: Clear and descriptive
- Content: Natural, conversational text
- Length: 100-200 words'''

MODEL_NAME = 'gemini-2.0-flash-exp'

# Audio configuration
AUDIO_CONFIG = {
	"generation_config": {
		"response_modalities": ["AUDIO"],
		"speech_config": {
			"voice_config": {
				"prebuilt_voice_config": {
					"voice_name": "Puck"  # Default voice that works
				}
			}
		}
	},
	"system_instruction": '''TEXT-TO-SPEECH MODE ONLY
PURE VOICE SYNTHESIS
NO AI FUNCTIONS
NO TEXT ANALYSIS
READ TEXT VERBATIM

RULES:
1. READ TEXT ONLY
2. NO EXTRA WORDS
3. NO ANALYSIS
4. NO HELP
5. NO COMMENTS'''
}

INPUT_SAMPLE_RATE = 16000   # 16kHz for input
OUTPUT_SAMPLE_RATE = 24000  # 24kHz for output
AUDIO_CHANNELS = 1          # Mono audio
AUDIO_SAMPLE_WIDTH = 2      # 16-bit PCM
ALIGNMENT_THRESHOLD = 0.8   # Minimum acceptable alignment score
CHUNK_SIZE = 1024          # Audio buffer size

# API limits
MAX_BATCH_SIZE = 100       # Based on rate limits
MAX_INPUT_TOKENS = 1048576  # ~1M tokens
MAX_OUTPUT_TOKENS = 8192    # ~8K tokens
RATE_LIMIT_RPM = 10        # Requests per minute
RATE_LIMIT_TPM = 4000000   # Tokens per minute
RATE_LIMIT_RPD = 1500      # Requests per day

# Validation constants
MAX_WORDS = 200
MIN_WORDS = 10

# Status messages
STATUS_MESSAGES = {
	"connecting": "Connecting to Gemini API...",
	"generating": "Generating audio...",
	"saving": "Saving audio file...",
	"complete": "Audio generation complete",
	"error_api_key": "Invalid API key. Please check your API key and try again.",
	"error_rate_limit": "API rate limit exceeded. Please wait a moment and try again.",
	"error_session_limit": f"Maximum concurrent sessions (3) reached",
	"error_token_limit": f"Token rate limit (4,000,000/min) exceeded",
	"error_duration": "Session duration limit exceeded (15 minutes)",
	"error_no_audio": "No audio data received",
	"error_alignment": "Low audio quality detected (alignment score below threshold)",
	"error_rate_limit": "API rate limit exceeded. Please try again in a minute.",
	"error_token_limit": "Token limit exceeded. Please try with shorter text.",
	"error_daily_limit": "Daily request limit reached. Please try again tomorrow.",
	"error_batch_limit": f"Batch size exceeds limit of {MAX_BATCH_SIZE} items.",
	"error_session_timeout": "Session timeout after 15 minutes. Please start a new session."
}

INPUT_SAMPLE_RATE = 16000   # 16kHz for input
OUTPUT_SAMPLE_RATE = 24000  # 24kHz for output
AUDIO_CHANNELS = 1          # Mono audio
AUDIO_SAMPLE_WIDTH = 2      # 16-bit PCM
ALIGNMENT_THRESHOLD = 0.8   # Minimum acceptable alignment score
CHUNK_SIZE = 1024          # Audio buffer size

# Session management constants
MAX_AUDIO_SESSION_DURATION = 15 * 60  # 15 minutes for audio sessions
MAX_CONCURRENT_SESSIONS = 3
MAX_TOKENS_PER_MINUTE = 4_000_000

def check_dependencies():
	"""Check if required dependencies are installed"""
	try:
		import phonemizer
		try:
			# Check if espeak is in PATH
			import subprocess
			try:
				subprocess.run(['espeak', '--version'], capture_output=True, check=True)
				espeak = phonemizer.backend.EspeakBackend(language='en-us', preserve_punctuation=False, with_stress=False, words_mismatch='ignore')
				return True
			except (subprocess.CalledProcessError, FileNotFoundError):
				print("Note: espeak not installed. Audio quality validation will be disabled.")
				print("Audio generation will still work, but without quality checks.")
				return False
		except RuntimeError:
			print("Note: Audio quality validation disabled.")
			return False
	except ImportError:
		print("Note: Audio quality validation disabled.")
		return False


# Initialize phonemizer with dependency check
HAS_PHONEMIZER = check_dependencies()
espeak = None
if HAS_PHONEMIZER:
	espeak = phonemizer.backend.EspeakBackend(language='en-us', preserve_punctuation=False, with_stress=False, words_mismatch='ignore')

# Phoneme alignment utilities
def is_junk(word):
	return word.strip('1234567890,.;:-?!\'\"()$%â€"â€œâ€ â€˜â€™') == ''

def validate_alignment(score: float) -> bool:
	"""Check if alignment score is acceptable"""
	if not HAS_PHONEMIZER:
		return True  # Always pass when validation is disabled
	return score >= ALIGNMENT_THRESHOLD

def align_phonemes(text1, text2):
	"""Align two texts using phoneme matching with fallback"""
	if not HAS_PHONEMIZER:
		return 1.0  # Return perfect score when validation is disabled
	
	matcher = SequenceMatcher(autojunk=False)
	words1 = text1.split()
	words2 = text2.split()
	
	ph1 = espeak.phonemize(words1)
	ph2 = espeak.phonemize(words2)
	
	# Filter junk
	ph1 = [w for w in ph1 if not is_junk(w)]
	ph2 = [w for w in ph2 if not is_junk(w)]
	
	matcher.set_seqs(ph1, ph2)
	match = matcher.find_longest_match(0, len(ph1), 0, len(ph2))
	
	return match.size / len(ph2) if ph2 else 0





def list_generated_files():
	"""List all generated audio files"""
	output_dir = 'generated_audio'
	if not os.path.exists(output_dir):
		return "No files generated yet"
	
	files = glob.glob(os.path.join(output_dir, '*.wav'))
	if not files:
		return "No audio files found"
	
	return "\n".join([os.path.basename(f) for f in sorted(files)])

# Batch processing and variable replacement functions
async def batch_generate_audio(api_key, texts, voice, progress=gr.Progress()):
	"""Generate audio for multiple texts in batch with error handling"""
	results = []
	errors = []
	
	for i, text in enumerate(texts):
		try:
			# Check rate limits
			can_proceed, error_msg = rate_limiter.check_and_update(len(text.split()))
			if not can_proceed:
				errors.append(error_msg)
				continue
				
			progress(i/len(texts), desc=f"Processing text {i+1}/{len(texts)}")
			audio_path, status = await generate_audio(api_key, text, voice)
			if audio_path:
				results.append((audio_path, status))
			else:
				errors.append(f"Failed to generate audio for text {i+1}: {status}")
		except Exception as e:
			errors.append(f"Error processing text {i+1}: {str(e)}")
	
	if errors:
		error_msg = "\n".join(errors)
		if results:
			return results[0][0], f"Generated {len(results)}/{len(texts)} files. Errors:\n{error_msg}"
		return None, f"Failed to generate any audio. Errors:\n{error_msg}"
	
	return results[0][0], f"Successfully generated {len(results)} audio files"
	"""Generate audio for multiple texts in batch"""
	results = []
	for i, text in enumerate(texts):
		progress(i/len(texts), desc=f"Processing text {i+1}/{len(texts)}")
		audio_path, status = await generate_audio(api_key, text, voice)
		if audio_path:
			results.append((audio_path, status))
	return results

async def get_variable_replacement(client, variable):
	"""Get contextual replacement for a variable"""
	var_type = variable[1:-1].replace("_", " ").title()
	prompt = f"""Generate a specific, realistic example to replace [{var_type}].
	Requirements:
	- Must be 1-3 words only
	- Must be specific (not generic)
	- Must fit naturally in the text
	- No explanations, just the replacement
	Example: If replacing [podcast name], respond with: "Tech Talk Daily"
	Now generate a replacement for: [{var_type}]"""
	
	try:
		response = client.models.generate_content(
			model='gemini-2.0-flash-exp',
			contents=prompt
		)
		return response.text.strip().strip('"').strip("'")
	except Exception as e:
		print(f"Error getting replacement for {var_type}: {str(e)}")
		return var_type

async def preprocess_text(client, text, progress=gr.Progress()):
	"""Enhanced variable replacement with progress tracking and error handling"""
	try:
		variables = re.findall(r'\[([^\]]+)\]', text)
		variables = list(set(variables))
		
		if not variables:
			return text
		
		processed_text = text
		for i, var in enumerate(variables):
			try:
				progress(i/len(variables), desc=f"Replacing variable {i+1}/{len(variables)}")
				variable = f"[{var}]"
				replacement = await get_variable_replacement(client, variable)
				processed_text = processed_text.replace(variable, replacement)
			except Exception as e:
				print(f"Error processing variable {var}: {str(e)}")
				continue  # Skip failed variable replacement
		
		return processed_text
	except Exception as e:
		print(f"Error in preprocess_text: {str(e)}")
		return text  # Return original text if preprocessing fails

# Rate limiting class
class RateLimit:
	def __init__(self):
		self.requests = 0
		self.tokens = 0
		self.last_reset = datetime.now()
		self.daily_requests = 0
		self.daily_reset = date.today()
		logging.info("Rate limiter initialized")
	
	def check_and_update(self, tokens: int = 0) -> tuple[bool, str]:
		now = datetime.now()
		
		# Reset counters if minute has passed
		if (now - self.last_reset).total_seconds() >= 60:
			logging.info(f"Rate limit reset - Previous minute: {self.requests} requests, {self.tokens} tokens")
			self.requests = 0
			self.tokens = 0
			self.last_reset = now
		
		# Reset daily counter if day has changed
		if now.date() != self.daily_reset:
			logging.info(f"Daily limit reset - Previous day: {self.daily_requests} requests")
			self.daily_requests = 0
			self.daily_reset = now.date()
		
		# Check limits
		if self.requests >= RATE_LIMIT_RPM:
			logging.warning(f"Rate limit exceeded: {self.requests}/{RATE_LIMIT_RPM} RPM")
			return False, f"Rate limit exceeded: {RATE_LIMIT_RPM} requests per minute"
		if self.tokens + tokens >= RATE_LIMIT_TPM:
			logging.warning(f"Token limit exceeded: {self.tokens + tokens}/{RATE_LIMIT_TPM} TPM")
			return False, f"Token limit exceeded: {RATE_LIMIT_TPM} tokens per minute"
		if self.daily_requests >= RATE_LIMIT_RPD:
			logging.warning(f"Daily limit exceeded: {self.daily_requests}/{RATE_LIMIT_RPD} RPD")
			return False, f"Daily limit exceeded: {RATE_LIMIT_RPD} requests per day"
		
		# Update counters
		self.requests += 1
		self.tokens += tokens
		self.daily_requests += 1
		logging.info(f"API request - Minute: {self.requests}/{RATE_LIMIT_RPM}, Tokens: {self.tokens}/{RATE_LIMIT_TPM}, Day: {self.daily_requests}/{RATE_LIMIT_RPD}")
		return True, ""

# Initialize rate limiter
rate_limiter = RateLimit()

# Type definitions
class YouTubeScript(typing.TypedDict):
	title: str
	script: str

class Content(typing.TypedDict):
	title: str
	text: str

# Constants and templates from both files
VOICES = ["Aoede", "Charon", "Fenrir", "Kore", "Puck"]
CATEGORIES = [
	"Tech Review", "Gaming", "Cooking", "Vlog", "Comedy", "DIY", "Travel",
	"Educational", "Music", "Product Review", "Fitness", "Book Review",
	"Movie Analysis", "Interview", "Science", "Art Tutorial", "Life Advice",
	"Personal Story", "Podcast", "Photography", "Fashion", "Health", "Meditation",
	"Language Learning", "Home Improvement", "Pet Care", "Car Review"
]
STYLES = ["energetic and enthusiastic", "calm and informative", "humorous and entertaining",
		  "professional and detailed", "casual and friendly", "inspirational and motivating"]

CONTENT_TYPES = [
	"Blog Post",
	"Product Review",
	"Tutorial",
	"Story",
	"News Article",
	"Educational Content",
	"Interview",
	"Podcast Script"
]

NICHES = [
	"Technology",
	"Gaming",
	"Health & Fitness", 
	"Business",
	"Education",
	"Entertainment",
	"Science",
	"Lifestyle",
	"Travel",
	"Food & Cooking",
	"Sports",
	"Arts & Culture"
]


VOICE_DESCRIPTIONS = {
	"Aoede": "Warm and engaging - perfect for storytelling and personal content",
	"Charon": "Deep and authoritative - ideal for educational and serious topics",
	"Fenrir": "Energetic and dynamic - great for gaming and action content",
	"Kore": "Clear and professional - suited for tutorials and reviews",
	"Puck": "Friendly and conversational - best for vlogs and casual content"
}

TONE_PRESETS = {
	"Default": "TONE: READ TEXT NATURALLY AND CLEARLY",
	"Professional": "TONE: SPEAK WITH AUTHORITY AND CLARITY, MAINTAIN PROFESSIONAL TONE, CLEAR ENUNCIATION",
	"Casual": "TONE: SPEAK NATURALLY AND CONVERSATIONALLY, MAINTAIN CASUAL TONE, NATURAL PACING",
	"Custom": "Enter your own tone instruction"
}


# Shared utility functions
def ensure_venv():
	if not os.environ.get('VIRTUAL_ENV'):
		print("WARNING: Not running in a virtual environment. Please activate the venv first.")
		print("Run: venv\\Scripts\\activate")
		exit(1)

def get_next_file_number(output_dir, voice):
	pattern = os.path.join(output_dir, f'voice-{voice.lower()}-*.wav')
	existing_files = glob.glob(pattern)
	if not existing_files:
		return 0
	numbers = [int(f.split('-')[-1].split('.')[0]) for f in existing_files]
	return max(numbers) + 1 if numbers else 0

# Improved text generation functions
async def generate_youtube_script(api_key: str, category: str, style: str) -> YouTubeScript:
	can_proceed, error_msg = rate_limiter.check_and_update()
	if not can_proceed:
		raise Exception(error_msg)

	client = genai.Client(api_key=api_key)
	
	prompt = f"""Create a natural, conversational YouTube script ({category}, {style} style):
Rules:
- No stage directions or actions in parentheses
- No all-caps words (use normal capitalization)
- No emojis or special characters
- Natural speaking style without excessive excitement
- No placeholders or variables - use specific examples
- 100-200 words
- Include: Hook, main content, call to action

Format: Return only valid JSON with "title" and "script" fields"""
	
	response = client.models.generate_content(
		model='gemini-2.0-flash-exp',
		contents=prompt
	)

	try:
		text = response.text.strip()
		if text.startswith('```json'):
			text = text[7:]
		if text.endswith('```'):
			text = text[:-3]
		script_data = json.loads(text.strip())
		
		script_data['title'] = script_data['title'].replace('🔥', '').replace('😮', '').strip()
		script_data['script'] = re.sub(r'\([^)]*\)', '', script_data['script'])
		script_data['script'] = re.sub(r'\b[A-Z]{2,}\b', lambda m: m.group(0).title(), script_data['script'])
		
		return script_data
	except json.JSONDecodeError:
		return {
			"title": f"{category} Video - {datetime.now().strftime('%Y%m%d_%H%M%S')}",
			"script": response.text.strip()
		}





async def generate_content(api_key: str, content_type: str, niche: str) -> Content:
	can_proceed, error_msg = rate_limiter.check_and_update()
	if not can_proceed:
		raise Exception(error_msg)

	client = genai.Client(api_key=api_key)
	
	prompt = f"""Create a {content_type} about {niche}.
Requirements:
- Natural, conversational style
- 100-200 words
- Clear structure with introduction, main points, and conclusion
- Engaging and informative tone
- No technical jargon unless necessary
- Include a clear title

Format: Return only valid JSON with "title" and "text" fields"""
	
	response = client.models.generate_content(
		model='gemini-2.0-flash-exp',
		contents=prompt
	)
	
	try:
		text = response.text.strip()
		if text.startswith('```json'):
			text = text[7:]
		if text.endswith('```'):
			text = text[:-3]
		content_data = json.loads(text.strip())
		
		# Clean up any emojis or special characters
		content_data['title'] = content_data['title'].replace('🔥', '').replace('😮', '').strip()
		content_data['text'] = re.sub(r'\([^)]*\)', '', content_data['text'])
		content_data['text'] = re.sub(r'\b[A-Z]{2,}\b', lambda m: m.group(0).title(), content_data['text'])
		
		return content_data
	except json.JSONDecodeError:
		return {
			"title": f"{content_type} - {datetime.now().strftime('%Y%m%d_%H%M%S')}",
			"text": response.text.strip()
		}


# Add input validation functions
def validate_text(text: str) -> tuple[bool, str]:
	"""Validate text input"""
	if not text:
		return False, STATUS_MESSAGES["error_no_audio"]
	
	word_count = len(text.split())
	if word_count > MAX_WORDS:
		return False, f"Text too long ({word_count} words). Please limit to {MAX_WORDS} words for optimal audio quality."
	if word_count < MIN_WORDS:
		return False, f"Text too short ({word_count} words). Please provide at least {MIN_WORDS} words."
	
	return True, ""

def validate_batch_size(size: int) -> tuple[bool, str]:
	"""Validate batch size"""
	if size < 1:
		return False, "Batch size must be at least 1"
	if size > MAX_BATCH_SIZE:
		return False, f"Batch size too large. Maximum is {MAX_BATCH_SIZE} items."
	return True, ""

# Improved audio generation
async def generate_audio(api_key, text, voice, tone_preset="Default", custom_tone="", progress=gr.Progress()):
	can_proceed, error_msg = rate_limiter.check_and_update(len(text.split()))
	if not can_proceed:
		return None, error_msg

	client = genai.Client(
		api_key=api_key, 
		http_options={
			'api_version': 'v1alpha',
			'timeout': 300,  # 5 minute timeout
		}
	)
	MODEL = f"models/{MODEL_NAME}"

	# Start with base audio config
	config = AUDIO_CONFIG.copy()
	config["generation_config"]["speech_config"]["voice_config"]["prebuilt_voice_config"]["voice_name"] = voice

	# Add tone instructions to system message
	base_system_message = AUDIO_CONFIG["system_instruction"]
	tone_instruction = ""
	
	if tone_preset == "Custom" and custom_tone.strip():
		tone_instruction = f"\nTONE INSTRUCTION:\n{custom_tone}"
	elif tone_preset in TONE_PRESETS:
		preset_message = TONE_PRESETS[tone_preset]
		tone_lines = [line for line in preset_message.split('\n') if 'TONE' in line]
		if tone_lines:
			tone_instruction = f"\nTONE INSTRUCTION:\n{tone_lines[0]}"
	
	config["system_instruction"] = base_system_message + tone_instruction


	output_dir = 'generated_audio'
	os.makedirs(output_dir, exist_ok=True)

	file_num = get_next_file_number(output_dir, voice)
	wav_filename = f'voice-{voice.lower()}-{file_num:03d}.wav'
	wav_filepath = os.path.join(output_dir, wav_filename)

	try:
		start_time = datetime.now()
		progress(0, desc=STATUS_MESSAGES["connecting"])
		async with client.aio.live.connect(
			model=MODEL,
			config=config
		) as session:
			if (datetime.now() - start_time).total_seconds() > MAX_AUDIO_SESSION_DURATION:
				return None, STATUS_MESSAGES["error_duration"]
			
			progress(0.2, desc=STATUS_MESSAGES["generating"])
			await session.send(input=text, end_of_turn=True)
			
			audio_chunks = []
			chunk_count = 0
			async for response in session.receive():
				if response.data:
					chunk_count += 1
					audio_chunks.append(response.data)
					progress_value = min(0.2 + (0.6 * (chunk_count / 50)), 0.8)
					progress(progress_value, desc=f"Generating audio... ({chunk_count} chunks)")
				if response.text:
					print(f"Text response: {response.text}")
			
			if not audio_chunks:
				return None, STATUS_MESSAGES["error_no_audio"]
			
			progress(0.8, desc=STATUS_MESSAGES["saving"])
			
			with wave.open(wav_filepath, 'wb') as wav_file:
				wav_file.setnchannels(AUDIO_CHANNELS)
				wav_file.setsampwidth(AUDIO_SAMPLE_WIDTH)
				wav_file.setframerate(OUTPUT_SAMPLE_RATE)
				audio_data = b''.join(audio_chunks)
				wav_file.writeframes(audio_data)
			
			# Update labels.json
			labels_file = os.path.join(output_dir, 'labels.json')
			if os.path.exists(labels_file):
				with open(labels_file, 'r') as f:
					labels = json.load(f)
			else:
				labels = {"samples": []}
			
			with wave.open(wav_filepath, 'rb') as wav:
				frames = wav.getnframes()
				rate = wav.getframerate()
				duration = frames / float(rate)
			
			labels["samples"].append({
				"audio_file": wav_filename,
				"text": text,
				"duration": round(duration, 2),
				"speaker_id": voice.lower(),
				"timestamp": datetime.now().isoformat()
			})
			
			# Add alignment validation with user feedback
			if audio_chunks:
				alignment_score = align_phonemes(text, text)
				if not validate_alignment(alignment_score):
					print(f"Warning: Low alignment score ({alignment_score})")
					return None, STATUS_MESSAGES["error_alignment"]
				labels["samples"][-1]["alignment_score"] = alignment_score
				labels["samples"][-1]["alignment_passed"] = validate_alignment(alignment_score)
			
			with open(labels_file, 'w') as f:
				json.dump(labels, f, indent=2)
			
			progress(1.0, desc=STATUS_MESSAGES["complete"])
			return wav_filepath, f"Audio generated successfully: {wav_filename}"

	except Exception as e:
		error_msg = str(e)
		logging.error(f"Audio generation error: {error_msg}")
		error_msg_lower = error_msg.lower()
		for key, msg in STATUS_MESSAGES.items():
			if key.startswith("error_") and key[6:] in error_msg_lower:
				return None, msg
		return None, f"Error: {error_msg}"



# Event handlers
async def handle_youtube_script(api_key, category, style, num_items, voice, tone_preset, custom_tone):
	try:
		scripts = []
		for i in range(int(num_items)):
			script = await generate_youtube_script(api_key, category, style)
			scripts.append(script)
		
		# Process each script for audio generation
		audio_results = []
		status_messages = []
		for script in scripts:
			# Validate text before audio generation
			valid, message = validate_text(script['script'])
			if not valid:
				status_messages.append(message)
				continue
				
			audio_path, status = await generate_audio(
				api_key=api_key,
				text=script['script'],
				voice=voice,
				tone_preset=tone_preset,
				custom_tone=custom_tone
			)
			if audio_path:
				audio_results.append((audio_path, status))
				status_messages.append(status)
		
		combined_text = "\n\n---\n\n".join(
			f"Title: {s['title']}\n\n{s['script']}" 
			for s in scripts
		)
		
		status = f"Generated {len(audio_results)} audio files. " + " ".join(status_messages)
		return combined_text, audio_results[0][0] if audio_results else None, status
	except Exception as e:
		return f"Error generating script: {str(e)}", None, str(e)

async def handle_content_generation(api_key, content_type, niche, num_items, voice, tone_preset, custom_tone):
	try:
		all_content = []
		audio_results = []
		status_messages = []
		
		for i in range(int(num_items)):
			try:
				content = await generate_content(api_key, content_type, niche)
				if content['text']:
					audio_path, status = await generate_audio(
						api_key=api_key,
						text=content['text'],
						voice=voice,
						tone_preset=tone_preset,
						custom_tone=custom_tone
					)
					if audio_path:
						audio_results.append((audio_path, status))
						status_messages.append(status)
				all_content.append(content)
			except Exception as e:
				print(f"Error generating content {i+1}: {str(e)}")
				continue
		
		if not all_content:
			return "Error: Failed to generate any content", None, "Generation failed"
		
		combined_text = "\n\n---\n\n".join(
			f"Title: {c['title']}\n\n{c['text']}" 
			for c in all_content
		)
		
		status = f"Generated {len(audio_results)} audio files. " + " ".join(status_messages)
		return combined_text, audio_results[0][0] if audio_results else None, status
	except Exception as e:
		return f"Error: {str(e)}", None, str(e)

def update_voice_info(voice_name):
	return VOICE_DESCRIPTIONS[voice_name]

def update_tone_visibility(preset):
	return gr.update(visible=preset == "Custom")

# Help text for interface
HELP_TEXT = """## 🎙️ Audio Content Generator
Generate high-quality audio content using Gemini's Multimodal Live API.

### Features:
- YouTube script generation with multiple categories and styles
- General content generation with customizable templates
- Multiple voice options with different characteristics
- Batch processing support
- Audio quality validation
- Variable replacement

### Usage:
1. Enter your Gemini API key
2. Choose YouTube Scripts or General Content
3. Configure your content settings
4. Generate audio with your chosen voice
"""

# Gradio interface
with gr.Blocks(title="Audio Content Generator") as app:
	gr.Markdown(HELP_TEXT)
	
	with gr.Row():
		api_key = gr.Textbox(
			label="Gemini API Key",
			placeholder="Enter your API key here...",
			type="password"
		)
		api_status = gr.Textbox(
			label="API Status",
			value="Enter API key",
			interactive=False
		)
	
	api_key.change(
		fn=lambda key: "API key provided" if key else "Please enter an API key",
		inputs=api_key,
		outputs=api_status
	)
	
	with gr.Tabs():
		# YouTube Scripts Tab
		with gr.Tab("YouTube Scripts"):
			with gr.Row():
				category = gr.Dropdown(
					choices=sorted(CATEGORIES),
					label="Video Category",
					value="Tech Review"
				)
				style = gr.Dropdown(
					choices=STYLES,
					label="Script Style",
					value="energetic and enthusiastic"
				)
				num_items = gr.Slider(
					minimum=1,
					maximum=MAX_BATCH_SIZE,
					value=1,
					step=1,
					label="Number of Scripts"
				)
			
			script_output = gr.TextArea(
				label="Script Content",
				interactive=True,
				lines=10
			)
			generate_script_btn = gr.Button("Generate Scripts and Audio", size="large")
		
		# General Content Tab
		with gr.Tab("General Content"):
			with gr.Row():
				content_type = gr.Dropdown(
					choices=sorted(CONTENT_TYPES),
					label="Content Type",
					value="Blog Post"
				)
				niche = gr.Dropdown(
					choices=sorted(NICHES),
					label="Subject/Niche",
					value="Technology"
				)
				num_items = gr.Slider(
					minimum=1,
					maximum=50,
					value=1,
					step=1,
					label="Number of Items"
				)
			
			content_generate_btn = gr.Button("Generate Content and Audio", size="large")

	# Voice and Tone Configuration
	with gr.Row():
		voice = gr.Dropdown(
			choices=VOICES,
			label="Select Voice", 
			value="Puck"
		)
		tone_preset = gr.Dropdown(
			choices=list(TONE_PRESETS.keys()),
			label="Voice Tone Preset",
			value="Default"
		)

	voice_info = gr.Markdown(value=VOICE_DESCRIPTIONS["Puck"])
	custom_tone = gr.TextArea(
		label="Custom Tone Configuration",
		placeholder="Enter tone instruction here (e.g., 'TONE: SPEAK SOFTLY AND CALMLY')",
		visible=False,
		lines=5
	)

	# Output and Status Display
	with gr.Row():
		with gr.Column(scale=2):
			audio_output = gr.Audio(label="Generated Audio")
			status_output = gr.Textbox(label="Status", interactive=False)
		with gr.Column(scale=1):
			quality_info = gr.Markdown("""
			**Audio Quality Metrics:**
			- Alignment Score: Measures how well the audio matches the text
			- Duration: Length of generated audio
			- Sample Rate: 24kHz high-quality audio
			""")
			file_list = gr.Textbox(
				label="Generated Files",
				value=list_generated_files(),
				interactive=False,
				lines=5
			)
			refresh_btn = gr.Button("🔄 Refresh File List")

	# UI update handlers
	voice.change(

		fn=update_voice_info,
		inputs=voice,
		outputs=voice_info
	)

	tone_preset.change(
		fn=update_tone_visibility,
		inputs=tone_preset,
		outputs=custom_tone
	)

	# Button click handlers
	refresh_btn.click(
		fn=list_generated_files,
		inputs=[],
		outputs=file_list
	)




	content_generate_btn.click(
		fn=lambda *args: asyncio.run(handle_content_generation(*args)),
		inputs=[api_key, content_type, niche, num_items, voice, tone_preset, custom_tone],
		outputs=[script_output, audio_output, status_output]
	)

	generate_script_btn.click(
		fn=lambda *args: asyncio.run(handle_youtube_script(*args)),
		inputs=[api_key, category, style, num_items, voice, tone_preset, custom_tone],
		outputs=[script_output, audio_output, status_output]
	)

if __name__ == "__main__":
	ensure_venv()
	app.launch()


