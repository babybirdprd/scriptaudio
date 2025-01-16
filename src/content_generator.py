import json
import logging
from datetime import datetime
from google import genai
from .config import *

async def generate_youtube_script(api_key: str, category: str, style: str) -> dict:
	"""Generate a YouTube script with specified category and style"""
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
		script_data = json.loads(text.strip())
		
		# Clean up the response
		script_data['title'] = script_data['title'].replace('🔥', '').replace('😮', '').strip()
		script_data['script'] = script_data['script'].replace('(', '').replace(')', '')
		
		return script_data
	except json.JSONDecodeError:
		return {
			"title": f"{category} Video - {datetime.now().strftime('%Y%m%d_%H%M%S')}",
			"script": response.text.strip()
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