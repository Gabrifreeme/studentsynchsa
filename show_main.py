with open('main_snippet.txt', 'r', encoding='utf-8') as f:
    lines = f.read().splitlines()
for i, line in enumerate(lines[:60]):
    print(f'{i+1}: {line[:300]}')
