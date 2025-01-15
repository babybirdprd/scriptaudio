import os
import glob
import json
import re
from google import genai
import asyncio

async def get_variable_replacement(client, variable):
    """Use Gemini to get a contextual replacement for a variable"""
    MODEL = "models/gemini-pro"
    
    # Remove brackets and convert to title case for prompt
    var_type = variable[1:-1].replace("_", " ").title()
    
    prompt = f"""You are helping create YouTube scripts. I need a specific, realistic example of {var_type}.
    Give me just ONE example, no explanation. Keep it concise (1-3 words).
    For example:
    - If I ask for a [podcast name], you might say: "Tech Talk Daily"
    - If I ask for an [artist name], you might say: "Emma Thompson"
    - If I ask for an [animal], you might say: "Red Panda"
    
    Now, give me ONE example of: {var_type}"""
    
    response = await client.generate_content_async(prompt)
    replacement = response.text.strip().strip('"').strip("'")
    print(f"Replacing {variable} with: {replacement}")
    return replacement

async def process_script(client, script_text):
    """Find and replace all [variables] in a script"""
    # Find all unique variables
    variables = re.findall(r'\[([^\]]+)\]', script_text)
    variables = list(set(variables))  # Remove duplicates
    
    if not variables:
        return script_text
    
    print(f"\nFound variables: {variables}")
    
    # Replace each variable
    processed_text = script_text
    for var in variables:
        variable = f"[{var}]"
        replacement = await get_variable_replacement(client, variable)
        processed_text = processed_text.replace(variable, replacement)
    
    return processed_text

async def main(api_key):
    # Initialize Gemini client
    client = genai.Client(api_key=api_key)
    
    # Create processed_scripts directory
    os.makedirs('processed_scripts', exist_ok=True)
    
    # Process each script
    script_files = glob.glob(os.path.join('scripts', '*.txt'))
    total_scripts = len(script_files)
    print(f"Found {total_scripts} scripts to process")
    
    processed_scripts = []
    
    for i, script_file in enumerate(script_files, 1):
        print(f"\nProcessing {os.path.basename(script_file)} ({i}/{total_scripts})")
        
        # Read script
        with open(script_file, 'r') as f:
            script_text = f.read()
        
        # Process variables
        processed_text = await process_script(client, script_text)
        
        # Save processed script
        output_file = os.path.join('processed_scripts', os.path.basename(script_file))
        with open(output_file, 'w') as f:
            f.write(processed_text)
        
        processed_scripts.append({
            "original": script_file,
            "processed": output_file,
            "replacements": processed_text != script_text
        })
        
        print(f"Saved to {output_file}")
    
    # Save processing report
    report = {
        "total_scripts": total_scripts,
        "scripts_with_variables": sum(1 for s in processed_scripts if s["replacements"]),
        "processed_files": processed_scripts
    }
    
    with open('processing_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print("\nProcessing complete!")
    print(f"Processed scripts saved to: processed_scripts/")
    print(f"Processing report saved to: processing_report.json")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Preprocess scripts by replacing variables with Gemini-generated content')
    parser.add_argument('--api-key', required=True, help='Gemini API Key')
    
    args = parser.parse_args()
    asyncio.run(main(args.api_key))
