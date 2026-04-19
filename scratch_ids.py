import re

path=r'd:\tesis\jhire\frontend\app.js'
js = open(path, 'r', encoding='utf-8').read()
ids = set(re.findall(r'document\.getElementById\([\'"](.*?)[\'"]\)', js))
print('\n'.join(ids))
