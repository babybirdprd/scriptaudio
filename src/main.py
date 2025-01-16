import asyncio
import gradio as gr
import logging
from .audio_utils import generate_audio
from .content_generator import generate_youtube_script, generate_content
from .utils import RateLimit, validate_text, validate_batch_size, ensure_venv, list_generated_files
from .config import *

# Configure logging
logging.basicConfig(
	filename='api_usage.log',
	level=logging.INFO,
	format='%(asctime)s - %(levelname)s - %(message)s'
)

# Initialize rate limiter
rate_limiter = RateLimit()

async def handle_script_only(api_key, category, style, num_items):
	try:
		scripts = []
		for i in range(int(num_items)):
			script = await generate_youtube_script(api_key, category, style)
			scripts.append(script)
		
		combined_text = "\n\n---\n\n".join(
			f"Title: {s['title']}\n\n{s['script']}" 
			for s in scripts
		)
		return combined_text, "Generated scripts successfully"
	except Exception as e:
		return f"Error generating scripts: {str(e)}", str(e)

async def handle_audio_only(api_key, script_text, voice, tone_preset, custom_tone):
	try:
		if not script_text:
			return None, "No script provided"
			
		# Split scripts by separator and process each separately
		scripts = script_text.split("---")
		audio_results = []
		status_messages = []
		
		for script in scripts:
			script = script.strip()
			if not script:
				continue
				
			# Extract just the script content, removing title if present
			if "Title:" in script:
				script = script.split("\n\n", 1)[1]
			
			valid, message = validate_text(script)
			if not valid:
				status_messages.append(message)
				continue
				
			audio_path, status = await generate_audio(
				api_key=api_key,
				text=script,
				voice=voice,
				tone_preset=tone_preset,
				custom_tone=custom_tone
			)
			if audio_path:
				audio_results.append((audio_path, status))
				status_messages.append(status)
		
		if not audio_results:
			return None, "No audio files generated"
			
		status = f"Generated {len(audio_results)} audio files. " + " ".join(status_messages)
		return audio_results[0][0], status
	except Exception as e:
		return None, str(e)

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
"""

async def handle_youtube_script(api_key, category, style, num_items, voice, tone_preset, custom_tone):
	try:
		scripts = []
		audio_results = []
		status_messages = []
		latest_audio = None
		
		# Generate scripts with progress updates
		for i in range(int(num_items)):
			script = await generate_youtube_script(api_key, category, style)
			scripts.append(script)
			# Update UI after each script is generated
			yield (
				"\n\n---\n\n".join(f"Title: {s['title']}\n\n{s['script']}" for s in scripts),
				latest_audio,
				f"Generated {len(scripts)} scripts..."
			)
		
		# Process audio generation with progress updates
		for i, script in enumerate(scripts):
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
				latest_audio = audio_path
				
				yield (
					"\n\n---\n\n".join(f"Title: {s['title']}\n\n{s['script']}" for s in scripts),
					latest_audio,
					f"Script generation complete. Converting to audio: {i+1}/{len(scripts)} scripts. " + " ".join(status_messages[-1:])
				)
		
		final_status = f"Completed: Generated {len(scripts)} scripts and {len(audio_results)} audio files."
		if status_messages:
			final_status += " Latest: " + status_messages[-1]
			
		yield (
				"\n\n---\n\n".join(f"Title: {s['title']}\n\n{s['script']}" for s in scripts),
				latest_audio,
				final_status
			)
			
	except Exception as e:
		yield f"Error generating script: {str(e)}", None, str(e)

async def handle_content_only(api_key, content_type, niche, num_items):
	try:
		all_content = []
		for i in range(int(num_items)):
			content = await generate_content(api_key, content_type, niche)
			all_content.append(content)
		
		combined_text = "\n\n---\n\n".join(
			f"Title: {c['title']}\n\n{c['text']}" 
			for c in all_content
		)
		return combined_text, "Generated content successfully"
	except Exception as e:
		return f"Error: {str(e)}", str(e)

async def handle_content_generation(api_key, content_type, niche, num_items, voice, tone_preset, custom_tone):
	try:
		all_content = []
		audio_results = []
		status_messages = []
		latest_audio = None
		
		# Generate content with progress updates
		for i in range(int(num_items)):
			content = await generate_content(api_key, content_type, niche)
			if content['text']:
				all_content.append(content)
				# Update UI after each content piece is generated
				yield (
					"\n\n---\n\n".join(f"Title: {c['title']}\n\n{c['text']}" for c in all_content),
					latest_audio,
					f"Generated {len(all_content)} content pieces..."
				)
		
		# Process audio generation with progress updates
		for i, content in enumerate(all_content):
			valid, message = validate_text(content['text'])
			if not valid:
				status_messages.append(message)
				continue
				
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
				latest_audio = audio_path
				
				yield (
					"\n\n---\n\n".join(f"Title: {c['title']}\n\n{c['text']}" for c in all_content),
					latest_audio,
					f"Content generation complete. Converting to audio: {i+1}/{len(all_content)} pieces. " + " ".join(status_messages[-1:])
				)
		
		final_status = f"Completed: Generated {len(all_content)} content pieces and {len(audio_results)} audio files."
		if status_messages:
			final_status += " Latest: " + status_messages[-1]
			
		yield (
			"\n\n---\n\n".join(f"Title: {c['title']}\n\n{c['text']}" for c in all_content),
			latest_audio,
			final_status
		)
			
	except Exception as e:
		yield f"Error: {str(e)}", None, str(e)

def update_voice_info(voice_name):
	return VOICE_DESCRIPTIONS[voice_name]

def update_tone_visibility(preset):
	return gr.update(visible=preset == "Custom")

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
					label="Number of Scripts to Generate",
					interactive=True,
					elem_id="youtube_batch_size",
					container=True,
					show_label=True
				)
			
			script_output = gr.TextArea(
				label="Script Content",
				interactive=True,
				lines=10
			)
			
			with gr.Row():
				generate_script_only_btn = gr.Button("Generate Scripts Only", size="large")
				generate_audio_only_btn = gr.Button("Generate Audio from Script", size="large", visible=True)
				generate_both_btn = gr.Button("Generate Scripts and Audio", size="large")
		
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
					maximum=MAX_BATCH_SIZE,
					value=1,
					step=1,
					label="Number of Items",
					interactive=True
				)
			
			content_output = gr.TextArea(
				label="Generated Content",
				interactive=True,
				lines=10
			)
			
			with gr.Row():
				generate_content_only_btn = gr.Button("Generate Content Only", size="large")
				generate_content_audio_btn = gr.Button("Generate Audio from Content", size="large", visible=True)
				generate_content_both_btn = gr.Button("Generate Content and Audio", size="large")

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

	refresh_btn.click(
		fn=list_generated_files,
		inputs=[],
		outputs=file_list
	)

	generate_content_only_btn.click(
		fn=handle_content_only,
		inputs=[api_key, content_type, niche, num_items],
		outputs=[content_output, status_output]
	)

	generate_content_audio_btn.click(
		fn=handle_audio_only,
		inputs=[api_key, content_output, voice, tone_preset, custom_tone],
		outputs=[audio_output, status_output]
	)

	generate_content_both_btn.click(
		fn=handle_content_generation,
		inputs=[api_key, content_type, niche, num_items, voice, tone_preset, custom_tone],
		outputs=[content_output, audio_output, status_output],
		show_progress=True
	)

	generate_script_only_btn.click(
		fn=handle_script_only,
		inputs=[api_key, category, style, num_items],
		outputs=[script_output, status_output]
	)

	generate_audio_only_btn.click(
		fn=handle_audio_only,
		inputs=[api_key, script_output, voice, tone_preset, custom_tone],
		outputs=[audio_output, status_output]
	)

	generate_both_btn.click(
		fn=handle_youtube_script,
		inputs=[api_key, category, style, num_items, voice, tone_preset, custom_tone],
		outputs=[script_output, audio_output, status_output],
		show_progress=True
	)

if __name__ == "__main__":
	ensure_venv()
	app.launch()