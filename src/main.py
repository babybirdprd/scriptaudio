import asyncio
import gradio as gr
import logging
from datetime import datetime
from .utils import RateLimit, validate_text, validate_batch_size, ensure_venv, list_generated_files
from .audio_utils import generate_audio
from .content_generator import generate_youtube_script, generate_content
from .config import *

# Initialize rate limiter
rate_limiter = RateLimit()

# Configure logging
logging.basicConfig(
	filename='api_usage.log',
	level=logging.INFO,
	format='%(asctime)s - %(levelname)s - %(message)s'
)


async def handle_script_only(api_key, category, style, num_items):
	try:
		batch_id = f"script_only_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
		scripts = []
		status_messages = []
		
		for i in range(int(num_items)):
			# Check rate limits with batch tracking
			valid, message = await rate_limiter.check_and_update(tokens=0, batch_id=batch_id)
			if not valid:
				return f"Error: {message}", message
			elif message:
				status_messages.append(message)
			
			script = await generate_youtube_script(api_key, category, style)
			if script and 'title' in script and 'script' in script:
				scripts.append(script)
		
		if not scripts:
			return "No scripts were generated successfully", "Failed to generate scripts"
			
		combined_text = "\n\n---\n\n".join(
			f"Title: {s['title']}\n\n{s['script']}" 
			for s in scripts
		)
		status = f"Generated {len(scripts)} scripts successfully"
		if status_messages:
			status += f" (with rate limiting delays)"
		return combined_text, status
	except Exception as e:
		return f"Error generating scripts: {str(e)}", str(e)

async def handle_audio_only(api_key, script_text, voice, tone_preset, custom_tone):
	try:
		if not script_text:
			return tuple([None] * 10 + ["No script provided"])
			
		batch_id = f"audio_only_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
		scripts = script_text.split("---")
		audio_files = []
		status_messages = []
		
		for script in scripts:
			script = script.strip()
			if not script:
				continue
				
			if "Title:" in script:
				script = script.split("\n\n", 1)[1]
			
			valid, message = validate_text(script)
			if not valid:
				status_messages.append(message)
				continue
			
			# Check rate limits before audio generation
			valid, message = await rate_limiter.check_and_update(tokens=0, batch_id=batch_id)
			if not valid:
				status_messages.append(message)
				break
			elif message:
				status_messages.append(message)
				
			audio_path, status = await generate_audio(
				api_key=api_key,
				text=script,
				voice=voice,
				tone_preset=tone_preset,
				custom_tone=custom_tone
			)
			if audio_path:
				audio_files.append(audio_path)
				status_messages.append(status)
		
		if not audio_files:
			return tuple([None] * 10 + ["No audio files generated"])
			
		# Create audio updates
		audio_updates = [None] * 10
		for j in range(len(audio_files)):
			if j < 10:
				audio_updates[j] = audio_files[j]
		
		status = f"Generated {len(audio_files)} audio files."
		if status_messages:
			status += " " + " ".join(status_messages)
		return tuple(audio_updates + [status])
	except Exception as e:
		return tuple([None] * 10 + [str(e)])


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
		# Validate batch size first
		valid, message = validate_batch_size(num_items)
		if not valid:
			yield tuple(
				[message] +
				[None] * 10 +
				[message]
			)
			return

		# Generate a unique batch ID
		batch_id = f"youtube_script_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
		scripts = []
		audio_files = []
		status_messages = []
		
		# Generate scripts with progress updates
		for i in range(int(num_items)):
			try:
				# Check rate limits with batch tracking
				valid, message = await rate_limiter.check_and_update(tokens=0, batch_id=batch_id)
				if not valid:
					status_messages.append(message)
					yield tuple(
						["\n\n---\n\n".join(f"Title: {s['title']}\n\n{s['script']}" for s in scripts)] +
						[None] * 10 +
						[message]
					)
					return
				elif message:  # Rate limit delay message
					status_messages.append(message)
					yield tuple(
						["\n\n---\n\n".join(f"Title: {s['title']}\n\n{s['script']}" for s in scripts)] +
						[None] * 10 +
						[f"Processing {i+1}/{num_items} scripts. {message}"]
					)

				script = await generate_youtube_script(api_key, category, style)
				if script and 'title' in script and 'script' in script:
					scripts.append(script)
					# Update UI with empty audio components
					audio_updates = [None] * 10
					yield tuple(
						["\n\n---\n\n".join(f"Title: {s['title']}\n\n{s['script']}" for s in scripts)] +
						audio_updates +
						[f"Generated {len(scripts)}/{num_items} scripts..."]
					)
			except Exception as script_error:
				logging.error(f"Error generating script {i+1}: {str(script_error)}")
				status_messages.append(f"Failed to generate script {i+1}: {str(script_error)}")
				continue
		
		if not scripts:
			yield tuple(
				["No scripts were generated successfully"] +
				[None] * 10 +
				["Failed to generate any scripts"]
			)
			return

		# Process audio generation with progress updates
		for i, script in enumerate(scripts):
			try:
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
					audio_files.append(audio_path)
					status_messages.append(status)
					
					# Update audio components
					audio_updates = [None] * 10
					for j in range(len(audio_files)):
						if j < 10:
							audio_updates[j] = audio_files[j]
					
					yield tuple(
						["\n\n---\n\n".join(f"Title: {s['title']}\n\n{s['script']}" for s in scripts)] +
						audio_updates +
						[f"Processing {i+1}/{len(scripts)} scripts. {status_messages[-1] if status_messages else ''}"]
					)
			except Exception as audio_error:
				logging.error(f"Error generating audio for script {i+1}: {str(audio_error)}")
				status_messages.append(f"Failed to generate audio for script {i+1}: {str(audio_error)}")
				continue
		
		final_status = f"Completed: Generated {len(scripts)}/{num_items} scripts and {len(audio_files)} audio files."
		if status_messages:
			final_status += f" Latest: {status_messages[-1]}"
		
		# Final yield with all generated content
		audio_updates = [None] * 10
		for j in range(len(audio_files)):
			if j < 10:
				audio_updates[j] = audio_files[j]
		
		yield tuple(
			["\n\n---\n\n".join(f"Title: {s['title']}\n\n{s['script']}" for s in scripts)] +
			audio_updates +
			[final_status]
		)
			
	except Exception as e:
		logging.error(f"Error in handle_youtube_script: {str(e)}")
		yield tuple(
			[f"Error: {str(e)}"] +
			[None] * 10 +
			[str(e)]
		)



async def handle_content_only(api_key, content_type, niche, num_items):
	try:
		batch_id = f"content_only_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
		all_content = []
		status_messages = []
		
		for i in range(int(num_items)):
			# Check rate limits with batch tracking
			valid, message = await rate_limiter.check_and_update(tokens=0, batch_id=batch_id)
			if not valid:
				return f"Error: {message}", message
			elif message:
				status_messages.append(message)
			
			content = await generate_content(api_key, content_type, niche)
			all_content.append(content)
		
		combined_text = "\n\n---\n\n".join(
			f"Title: {c['title']}\n\n{c['text']}" 
			for c in all_content
		)
		status = "Generated content successfully"
		if status_messages:
			status += f" (with rate limiting delays)"
		return combined_text, status
	except Exception as e:
		return f"Error: {str(e)}", str(e)

async def handle_content_generation(api_key, content_type, niche, num_items, voice, tone_preset, custom_tone):
	try:
		batch_id = f"content_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
		all_content = []
		audio_files = []
		status_messages = []
		
		# Generate content with progress updates
		for i in range(int(num_items)):
			# Check rate limits with batch tracking
			valid, message = await rate_limiter.check_and_update(tokens=0, batch_id=batch_id)
			if not valid:
				status_messages.append(message)
				yield tuple(
					["\n\n---\n\n".join(f"Title: {c['title']}\n\n{c['text']}" for c in all_content)] +
					[None] * 10 +
					[message]
				)
				return
			elif message:  # Rate limit delay message
				status_messages.append(message)
				yield tuple(
					["\n\n---\n\n".join(f"Title: {c['title']}\n\n{c['text']}" for c in all_content)] +
					[None] * 10 +
					[f"Processing {i+1}/{num_items} items. {message}"]
				)

			content = await generate_content(api_key, content_type, niche)
			if content['text']:
				all_content.append(content)
				# Update UI with empty audio components
				audio_updates = [None] * 10
				yield tuple(["\n\n---\n\n".join(f"Title: {c['title']}\n\n{c['text']}" for c in all_content)] + 
						   audio_updates + 
						   [f"Generated {len(all_content)} content pieces..."])
		
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
				audio_files.append(audio_path)
				status_messages.append(status)
				
				# Update audio components
				audio_updates = [None] * 10
				for j in range(len(audio_files)):
					if j < 10:
						audio_updates[j] = audio_files[j]
				
				yield tuple(["\n\n---\n\n".join(f"Title: {c['title']}\n\n{c['text']}" for c in all_content)] + 
						   audio_updates + 
						   [f"Content generation complete. Converting to audio: {i+1}/{len(all_content)} pieces. " + " ".join(status_messages[-1:])])
		
		final_status = f"Completed: Generated {len(all_content)} content pieces and {len(audio_files)} audio files."
		if status_messages:
			final_status += " Latest: " + status_messages[-1]
		
		# Final yield with all generated content
		audio_updates = [None] * 10
		for j in range(len(audio_files)):
			if j < 10:
				audio_updates[j] = audio_files[j]
		
		yield tuple(["\n\n---\n\n".join(f"Title: {c['title']}\n\n{c['text']}" for c in all_content)] + 
					audio_updates + 
					[final_status])
			
	except Exception as e:
		yield tuple([f"Error: {str(e)}"] + [None] * 10 + [str(e)])



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
				youtube_num_items = gr.Slider(
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
				content_num_items = gr.Slider(
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
			with gr.Group() as audio_outputs:
				# Initialize audio components list
				audio_components = []
				for i in range(10):
					audio_components.append(gr.Audio(
						label=f"Generated Audio {i+1}",
						visible=True,
						interactive=False,
						show_label=True
					))
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
		inputs=[api_key, content_type, niche, content_num_items],
		outputs=[content_output, status_output]
	)

	generate_content_audio_btn.click(
		fn=handle_audio_only,
		inputs=[api_key, content_output, voice, tone_preset, custom_tone],
		outputs=audio_components + [status_output]
	)

	generate_content_both_btn.click(
		fn=handle_content_generation,
		inputs=[api_key, content_type, niche, content_num_items, voice, tone_preset, custom_tone],
		outputs=[content_output] + audio_components + [status_output],
		show_progress=True
	)

	generate_script_only_btn.click(
		fn=handle_script_only,
		inputs=[api_key, category, style, youtube_num_items],
		outputs=[script_output, status_output]
	)

	generate_audio_only_btn.click(
		fn=handle_audio_only,
		inputs=[api_key, script_output, voice, tone_preset, custom_tone],
		outputs=audio_components + [status_output]
	)

	generate_both_btn.click(
		fn=handle_youtube_script,
		inputs=[api_key, category, style, youtube_num_items, voice, tone_preset, custom_tone],
		outputs=[script_output] + audio_components + [status_output],
		show_progress=True
	)

if __name__ == "__main__":
	ensure_venv()
	app.launch()