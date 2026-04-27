import os

file_path = 'app.py'

if os.path.exists(file_path):
    # Read the file with UTF-8 encoding to handle emojis
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove the problematic "Table" word at the end
    # We also strip trailing whitespace to be safe
    new_content = content.strip().replace('Table', '')
    
    # Write it back safely
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ Successfully cleaned app.py and removed the stray 'Table' word.")
else:
    print("❌ Error: app.py not found in this folder.")