import json

from cryptography.hazmat.primitives import serialization

p = r'D:\projects\acesi\tools\vapid_keys.json'
with open(p, 'r', encoding='utf-8') as f:
    data = json.load(f)
key = serialization.load_pem_private_key(data['private'].encode(), password=None)
pem = key.private_bytes(
    serialization.Encoding.PEM,
    serialization.PrivateFormat.TraditionalOpenSSL,
    serialization.NoEncryption(),
).decode()
with open(r'D:\projects\acesi\tools\vapid_private.pem', 'w', encoding='utf-8') as f:
    f.write(pem)
print('wrote vapid_private.pem')
