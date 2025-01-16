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
		for i in range(int(num_items)):
			script = await generate_youtube_script(api_key, category, style)
			scripts.append(script)
		
		audio_results = []
		status_messages = []
		for script in scripts:
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
				logging.error(f"Error generating content {i+1}: {str(e)}")
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
					label="Number of Scripts"
				)
			
			script_output = gr.TextArea(
				label="Script Content",
				interactive=True,
				lines=10
			)
			generate_script_btn = gr.Button("Generate Scripts and Audio", size="large")
		
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