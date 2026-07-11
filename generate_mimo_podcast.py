import requests
import base64
import json
import os
import re
import time

MIMO_KEY = "sk-snm4nwfys0ras7h2o4jo74pq0rehi3t2bibunlo3wkwg90rf"
API_URL = "https://api.xiaomimimo.com/v1/chat/completions"

SCRIPT_FILE = r"D:\\hermes\\podcast\\script_usda_2026.txt"
OUTPUT_DIR = r"D:\\hermes\\podcast\\mimo_segments"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 讀取腳本
with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
    lines = f.readlines()

segments = []
current_speaker = None
current_text = []

for line in lines:
    line = line.strip()
    if line.startswith("==") and line.endswith("=="):
        if current_speaker and current_text:
            segments.append((current_speaker, "".join(current_text)))
        m = re.match(r"== (.+?)（", line)
        current_speaker = m.group(1) if m else None
        current_text = []
    elif line and current_speaker:
        current_text.append(line)

if current_speaker and current_text:
    segments.append((current_speaker, "".join(current_text)))

print(f"Total segments: {len(segments)}")

# Voice configs
VOICE_CONFIGS = {
    "小陳": {
        "model": "mimo-v2.5-tts",
        "style": "自然知性女聲，像知識型 podcast 主持人，咬字清晰，語氣真誠溫和",
        "voice": "mimo_default"
    },
    "雲哲": {
        "model": "mimo-v2.5-tts-voicedesign",
        "style": "溫暖沉穩的男聲，像深夜電台主持人，有磁性但不過度，語氣自然不僵硬",
        "voice": None
    }
}

headers = {
    "api-key": MIMO_KEY,
    "Content-Type": "application/json"
}

def call_tts(speaker, text):
    config = VOICE_CONFIGS[speaker]
    
    if config["model"] == "mimo-v2.5-tts":
        messages = [
            {"role": "user", "content": config["style"]},
            {"role": "assistant", "content": text}
        ]
        payload = {
            "model": config["model"],
            "messages": messages,
            "audio": {"format": "wav", "voice": config["voice"]}
        }
    else:
        # voicedesign
        messages = [
            {"role": "user", "content": config["style"]},
            {"role": "assistant", "content": text}
        ]
        payload = {
            "model": config["model"],
            "messages": messages,
            "audio": {"format": "wav"}
        }
    
    for attempt in range(3):
        try:
            resp = requests.post(API_URL, headers=headers, json=payload, timeout=60)
            data = resp.json()
            if "choices" in data:
                audio_b64 = data["choices"][0]["message"]["audio"]["data"]
                return base64.b64decode(audio_b64)
            elif "error" in data:
                print(f"  ❌ API Error: {data['error'].get('message', str(data['error']))}")
                return None
        except Exception as e:
            print(f"  ❌ Attempt {attempt+1} failed: {e}")
            time.sleep(2)
    return None

# Generate all segments
for i, (speaker, text) in enumerate(segments):
    output_file = os.path.join(OUTPUT_DIR, f"seg_{i:03d}_{speaker}.wav")
    
    # Skip if already exists
    if os.path.exists(output_file) and os.path.getsize(output_file) > 1000:
        print(f"  ⏭️ [{i}] {speaker}: already exists")
        continue
    
    print(f"  🎤 [{i}] {speaker} ({len(text)} chars)...", end="", flush=True)
    audio_data = call_tts(speaker, text)
    
    if audio_data:
        with open(output_file, "wb") as f:
            f.write(audio_data)
        print(f" ✅ {len(audio_data)} bytes")
    else:
        print(f" ❌ FAILED")
    
    # Rate limiting - short delay
    time.sleep(0.5)

print("\n✅ All segments generated in:", OUTPUT_DIR)
