import json
import os

# Create scripts directory if it doesn't exist
if not os.path.exists('scripts'):
    os.makedirs('scripts')

# Load and parse scripts
with open('script.json', 'r') as f:
    data = json.loads(f.read())
    scripts = json.loads(data["response"])

# Save each script to a separate file
for script in scripts:
    title = script["title"]
    # Clean filename - replace spaces and special chars
    filename = "".join(x for x in title if x.isalnum() or x in "- ").replace(" ", "_").lower()
    filepath = os.path.join('scripts', f"{filename}.txt")
    
    with open(filepath, 'w') as f:
        f.write(script["script"])
    print(f"Saved: {filepath}")

print(f"\nTotal scripts parsed: {len(scripts)}")
