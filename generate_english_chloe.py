import requests
import base64
import json
import os
import time

MIMO_KEY = "sk-snm4nwfys0ras7h2o4jo74pq0rehi3t2bibunlo3wkwg90rf"
API_URL = "https://api.xiaomimimo.com/v1/chat/completions"

SCRIPT_FILE = r"D:\\hermes\\podcast\\script_english_chloe.txt"
OUTPUT_DIR = r"D:\\hermes\\podcast\\en_segments"
os.makedirs(OUTPUT_DIR, exist_ok=True)

with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
    full_text = f.read().strip()

# Split into natural chunks
paragraphs = [p.strip() for p in full_text.split("\n\n") if p.strip()]
chunks = []
current = ""
for p in paragraphs:
    if len(current) + len(p) < 350:
        current += p + "\n\n"
    else:
        if current:
            chunks.append(current.strip())
        current = p + "\n\n"
if current:
    chunks.append(current.strip())

print(f"Total: {len(full_text)} chars, {len(chunks)} chunks")

headers = {
    "api-key": MIMO_KEY,
    "Content-Type": "application/json"
}

def call_tts(text, chunk_idx):
    payload = {
        "model": "mimo-v2.5-tts",
        "messages": [
            {"role": "user", "content": "Natural podcast host, warm and engaging, clear pronunciation, moderate pace, like a knowledgeable friend explaining something interesting"},
            {"role": "assistant", "content": text}
        ],
        "audio": {"format": "wav", "voice": "Chloe"}
    }
    
    for attempt in range(3):
        try:
            resp = requests.post(API_URL, headers=headers, json=payload, timeout=60)
            data = resp.json()
            if "choices" in data:
                audio_b64 = data["choices"][0]["message"]["audio"]["data"]
                return base64.b64decode(audio_b64)
            elif "error" in data:
                print(f"  ❌ Chunk {chunk_idx}: {data['error'].get('message', str(data['error']))}")
                return None
        except Exception as e:
            print(f"  ❌ Chunk {chunk_idx} attempt {attempt+1}: {e}")
            time.sleep(2)
    return None

for i, chunk_text in enumerate(chunks):
    output_file = os.path.join(OUTPUT_DIR, f"chunk_{i:03d}.wav")
    if os.path.exists(output_file) and os.path.getsize(output_file) > 1000:
        print(f"  ⏭️ [{i}] exists")
        continue
    print(f"  🎤 [{i}/{len(chunks)}] ({len(chunk_text)} chars)...", end="", flush=True)
    audio = call_tts(chunk_text, i)
    if audio:
        with open(output_file, "wb") as f:
            f.write(audio)
        print(f" ✅ {len(audio)} bytes")
    else:
        print(f" ❌ FAILED")
    time.sleep(0.5)

print("\n✅ Done!")
