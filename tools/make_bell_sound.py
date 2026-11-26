import math
import os
import struct
import wave

rate = 44100
duration = 0.95
hits = (0.0, 0.46)
frames = bytearray()

for i in range(int(rate * duration)):
    t = i / rate
    value = 0.0
    for start in hits:
        local = t - start
        if 0 <= local < 0.42:
            env = math.exp(-9.0 * local)
            tone = (
                math.sin(2 * math.pi * 880 * local) * 0.70
                + math.sin(2 * math.pi * 1320 * local) * 0.22
                + math.sin(2 * math.pi * 1760 * local) * 0.08
            )
            value += env * tone
    value = max(-1.0, min(1.0, value * 0.45))
    frames.extend(struct.pack('<h', int(value * 32767)))

out = r'C:\Users\gabri\Documents\LibSyncStudent\assets\audio\email_ding.wav'
os.makedirs(os.path.dirname(out), exist_ok=True)
with wave.open(out, 'wb') as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(rate)
    w.writeframes(bytes(frames))
print('wrote', out, len(frames), 'bytes')
