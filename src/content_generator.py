import json
import logging
from datetime import datetime
from google import genai
from .config import *

async def generate_youtube_script(api_key: str, category: str, style: str) -> dict:
	"""Generate a YouTube script with specified category and style"""
	client = genai.Client(api_key=api_key)
	
	prompt = f"""Create a YouTube script for {category} in {style} style.
Format the response as JSON with exactly this structure:
{{
	"title": "Video Title Here",
	"script": "Full script content here"
}}

Requirements:
- Natural, conversational script
- No stage directions or actions in parentheses
- No all-caps words
- No emojis or special characters
- 100-200 words
- Include hook, main content, and call to action
- Return ONLY valid JSON, no other text"""
	
	try:
		response = client.models.generate_content(
			model=MODEL,
			contents=prompt
		)

		text = response.text.strip()
		
		# Remove any markdown code block markers
		if text.startswith('```'):
			text = text.split('\n', 1)[1]
		if text.endswith('```'):
			text = text.rsplit('\n', 1)[0]
		
		# Remove any "json" language identifier
		if text.startswith('json'):
			text = text.split('\n', 1)[1]
			
		# Clean the text before JSON parsing
		text = text.strip()
		
		try:
			script_data = json.loads(text)
			
			# Validate required fields
			if not isinstance(script_data, dict) or 'title' not in script_data or 'script' not in script_data:
				raise ValueError("Invalid script format")
				
			# Clean up the response
			script_data['title'] = script_data['title'].replace('🔥', '').replace('😮', '').strip()
			script_data['script'] = script_data['script'].replace('(', '').replace(')', '').strip()
			
			if not script_data['title'] or not script_data['script']:
				raise ValueError("Empty title or script")
				
			return script_data
			
		except json.JSONDecodeError as je:
			logging.error(f"JSON parsing error: {str(je)}\nResponse text: {text}")
			# Attempt to create a structured response from unstructured text
			return {
				"title": f"{category} Video - {datetime.now().strftime('%Y%m%d_%H%M%S')}",
				"script": text
			}
			
	except Exception as e:
		logging.error(f"Error generating YouTube script: {str(e)}")
		raise

async def generate_content(api_key: str, content_type: str, niche: str) -> dict:
	"""Generate content with specified type and niche"""
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
	
	try:
		response = client.models.generate_content(
			model=MODEL,
			contents=prompt
		)
		
		text = response.text.strip()
		if text.startswith('```json'):
			text = text[7:]
		if text.endswith('```'):
			text = text[:-3]
		content_data = json.loads(text.strip())
		
		# Clean up the response
		content_data['title'] = content_data['title'].replace('🔥', '').replace('😮', '').strip()
		content_data['text'] = content_data['text'].replace('(', '').replace(')', '')
		
		return content_data
	except json.JSONDecodeError:
		return {
			"title": f"{content_type} - {datetime.now().strftime('%Y%m%d_%H%M%S')}",
			"text": response.text.strip()
		}
	except Exception as e:
		logging.error(f"Error generating content: {str(e)}")
		raise