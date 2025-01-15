import os
import json
import random
import typing_extensions as typing
import google.generativeai as genai

class YouTubeScript(typing.TypedDict):
    title: str
    script: str

def get_script_prompt(category: str, style: str) -> str:
    return f"""Create a YouTube script for a {category} video in a {style} style.
    
    Requirements:
    1. Title: Create a catchy, clickable title that accurately represents the content
    2. Script: Write an engaging script that:
       - Starts with a strong hook
       - Uses natural, conversational YouTube style
       - Includes audience engagement phrases
       - Is between 100-200 words
       - Ends with a clear call to action
       - Matches the {style} style
    
    Format the response as JSON with 'title' and 'script' fields.
    Make it sound authentic and enthusiastic, like a real YouTuber."""

def generate_scripts(api_key: str, num_scripts: int = 100) -> list[YouTubeScript]:
    # Initialize Gemini
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        'gemini-2.0-flash-exp',
        system_instruction="You are a YouTube script generator. Always format your response as valid JSON with 'title' and 'script' fields. Never include any additional text or formatting outside of the JSON structure."
    )
    
    # Categories and styles for variety
    categories = [
        "Tech Review", "Gaming", "Cooking", "Vlog", "Comedy", "DIY", "Travel",
        "Educational", "Music", "Product Review", "Fitness", "Book Review",
        "Movie Analysis", "Interview", "Science", "Art Tutorial", "Life Advice",
        "Fashion", "Photography", "Home Improvement", "Pet Care", "Gardening",
        "Language Learning", "Meditation", "Career Advice", "Financial Tips"
    ]
    
    styles = [
        "energetic and enthusiastic",
        "calm and informative",
        "humorous and entertaining",
        "professional and detailed",
        "casual and friendly",
        "inspirational and motivating",
        "quirky and fun",
        "serious and educational"
    ]
    
    scripts = []
    print(f"Generating {num_scripts} scripts...")
    
    for i in range(num_scripts):
        category = random.choice(categories)
        style = random.choice(styles)
        prompt = get_script_prompt(category, style)
        
        try:
            # Generate script with structured output
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.9,
                    max_output_tokens=2048,
                    response_mime_type="application/json",
                    response_schema=YouTubeScript
                )
            )
            
            try:
                script = json.loads(response.text)
                if not isinstance(script, dict) or 'title' not in script or 'script' not in script:
                    raise ValueError("Response missing required fields")
                scripts.append(script)
                print(f"Generated script {i+1}/{num_scripts}: {script['title']}")
            except json.JSONDecodeError:
                print(f"Error: Invalid JSON response for script {i+1}")
                raise
            
        except Exception as e:
            print(f"Error generating script {i+1}: {str(e)}")
            # Try one more time with a different category/style
            try:
                category = random.choice(categories)
                style = random.choice(styles)
                prompt = get_script_prompt(category, style)
                
                response = model.generate_content(
                    prompt,
                    generation_config=genai.GenerationConfig(
                        temperature=0.9,
                        max_output_tokens=2048,
                        response_mime_type="application/json",
                        response_schema=YouTubeScript
                    )
                )
                
                try:
                    script = json.loads(response.text)
                    if not isinstance(script, dict) or 'title' not in script or 'script' not in script:
                        raise ValueError("Response missing required fields")
                    scripts.append(script)
                    print(f"Retry successful for script {i+1}: {script['title']}")
                except json.JSONDecodeError:
                    print(f"Error: Invalid JSON response for retry of script {i+1}")
                    raise
                
            except Exception as e:
                print(f"Retry also failed for script {i+1}: {str(e)}")
                continue
    
    return scripts

def save_scripts(scripts: list[YouTubeScript], output_file: str = "generated_scripts.json"):
    """Save scripts in the same format as script.json"""
    # Get base name and extension
    base, ext = os.path.splitext(output_file)
    final_path = output_file
    counter = 0
    
    # If file exists, try incrementing numbers until we find an available filename
    while os.path.exists(final_path):
        counter += 1
        final_path = f"{base}_{counter}{ext}"
    
    # Convert scripts to JSON string with proper escaping
    scripts_json = json.dumps(scripts, ensure_ascii=False)
    
    # Create output object with the JSON string as response
    output = {
        "response": scripts_json
    }
    
    # Write output to file, ensuring proper escaping is maintained
    with open(final_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\nSaved {len(scripts)} scripts to {final_path}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate YouTube scripts using Gemini')
    parser.add_argument('--api-key', required=True, help='Gemini API Key')
    parser.add_argument('--num-scripts', type=int, default=100,
                      help='Number of scripts to generate (default: 100)')
    parser.add_argument('--output', default='generated_scripts.json',
                      help='Output JSON file (default: generated_scripts.json)')
    
    args = parser.parse_args()
    
    # Run the generator
    scripts = generate_scripts(args.api_key, args.num_scripts)
    save_scripts(scripts, args.output)
