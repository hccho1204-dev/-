import json, sys, os
d = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(d, 'src.html'), encoding='utf-8').read()
data = open(os.path.join(d, 'apis.json'), encoding='utf-8').read().replace('</', '<\\/')
body = src.replace('__APIS__', data)
open(sys.argv[1], 'w', encoding='utf-8').write(body)
full = '<!doctype html>\n<html lang="ko">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n</head>\n<body>\n' + body + '\n</body>\n</html>\n'
open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(full)
