import os

directory = r'd:\tesis\jhire\frontend'
for root, dirs, files in os.walk(directory):
    for file in files:
        if file.endswith('.html') or file.endswith('.js'):
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Replace http://localhost:8000 with empty string
            new_content = content.replace('http://localhost:8000', '')
            # Replace the specific websocket url 
            new_content = new_content.replace("'localhost:8000/api/dashboard/ws'", "window.location.host + '/api/dashboard/ws'")
            
            if new_content != content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f'Updated {filepath}')
