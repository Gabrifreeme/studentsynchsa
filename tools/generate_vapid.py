import base64
import json

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

key = ec.generate_private_key(ec.SECP256R1())
private_pem = key.private_bytes(
    serialization.Encoding.PEM,
    serialization.PrivateFormat.PKCS8,
    serialization.NoEncryption(),
).decode()
public_raw = key.public_key().public_bytes(
    serialization.Encoding.X962,
    serialization.PublicFormat.UncompressedPoint,
)
public_b64 = base64.urlsafe_b64encode(public_raw).decode().rstrip('=')

out = r'D:\projects\acesi\tools\vapid_keys.json'
with open(out, 'w', encoding='utf-8') as f:
    json.dump({'public': public_b64, 'private': private_pem}, f)
print('public:', public_b64)
print('saved', out)
