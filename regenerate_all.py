import requests
import base64
import json
import os
import time

MIMO_KEY = "sk-snm4nwfys0ras7h2o4jo74pq0rehi3t2bibunlo3wkwg90rf"
API_URL = "https://api.xiaomimimo.com/v1/chat/completions"
BASE_DIR = r"D:\\hermes\\podcast"

headers = {
    "api-key": MIMO_KEY,
    "Content-Type": "application/json"
}

def call_tts(text, chunk_idx, label):
    payload = {
        "model": "mimo-v2.5-tts",
        "messages": [
            {"role": "user", "content": "自然知性女聲，像知識型 podcast 主持人 Julie，咬字清晰，語氣真誠溫柔，語速適中"},
            {"role": "assistant", "content": text}
        ],
        "audio": {"format": "wav", "voice": "mimo_default"}
    }
    
    for attempt in range(3):
        try:
            resp = requests.post(API_URL, headers=headers, json=payload, timeout=60)
            data = resp.json()
            if "choices" in data:
                audio_b64 = data["choices"][0]["message"]["audio"]["data"]
                return base64.b64decode(audio_b64)
            elif "error" in data:
                print(f"  ❌ [{label}] Chunk {chunk_idx}: {data['error'].get('message', str(data['error']))}")
                return None
        except Exception as e:
            print(f"  ❌ [{label}] Chunk {chunk_idx} attempt {attempt+1}: {e}")
            time.sleep(2)
    return None

def process_script(script_file, output_dir, label):
    out_dir = os.path.join(BASE_DIR, output_dir)
    os.makedirs(out_dir, exist_ok=True)
    
    with open(os.path.join(BASE_DIR, script_file), "r", encoding="utf-8") as f:
        full_text = f.read().strip()
    
    paragraphs = [p.strip() for p in full_text.split("\n\n") if p.strip()]
    chunks = []
    current = ""
    for p in paragraphs:
        if len(current) + len(p) < 300:
            current += p + "\n\n"
        else:
            if current:
                chunks.append(current.strip())
            current = p + "\n\n"
    if current:
        chunks.append(current.strip())
    
    print(f"\n🎬 [{label}] {len(full_text)} chars, {len(chunks)} chunks")
    
    for i, chunk_text in enumerate(chunks):
        output_file = os.path.join(out_dir, f"chunk_{i:03d}.wav")
        print(f"  🎤 [{label}] [{i}/{len(chunks)}] ({len(chunk_text)} chars)...", end="", flush=True)
        audio = call_tts(chunk_text, i, label)
        if audio:
            with open(output_file, "wb") as f:
                f.write(audio)
            print(f" ✅ {len(audio)} bytes")
        else:
            print(f" ❌")
        time.sleep(0.3)
    
    return chunks

# Regenerate EP3-EP7 (scripts now say "Andy熱愛的新聞小知識")
process_script("script_glp1_zh.txt", "glp1_seg_v2", "EP3 GLP-1")
process_script("script_gpt56_zh.txt", "gpt56_seg_v2", "EP4 GPT-5.6")
process_script("script_apple_openai_zh.txt", "apple_seg_v2", "EP5 Apple")
process_script("script_bone_sugar_zh.txt", "bone_seg_v2", "EP6 骨骼")
process_script("script_root_canal_zh.txt", "root_seg_v2", "EP7 根管")

print("\n✅ All done!")
