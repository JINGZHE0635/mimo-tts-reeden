#!/usr/bin/env python3
"""MiMo TTS bridge for Hermes command provider.

Called by Hermes tts command provider with placeholders:
  mimo-tts.py {input_path} {output_path} {voice} {model}

Reads text from input file, calls Xiaomi MiMo TTS (OpenAI-compatible
chat/completions with audio field), writes MP3 to output_path.

Env: MIMO_API_KEY (sk- or tp- prefix) or MIMO_METERED_API_KEY; optional
MIMO_BASE_URL (default token-plan-cn for tp- keys, api.xiaomimimo.com otherwise).
"""
import base64
import json
import os
import sys
import urllib.request
import urllib.error

def main() -> int:
    if len(sys.argv) < 3:
        print("usage: mimo-tts.py <input_path> <output_path> [voice] [model]", file=sys.stderr)
        return 2
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    voice = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] else "茉莉"
    model = sys.argv[4] if len(sys.argv) > 4 and sys.argv[4] else "mimo-v2.5-tts"

    with open(input_path, encoding="utf-8") as f:
        text = f.read().strip()
    if not text:
        print("empty input text", file=sys.stderr)
        return 2

    api_key = os.environ.get("MIMO_API_KEY") or os.environ.get("MIMO_METERED_API_KEY") or ""
    if not api_key:
        print("MIMO_API_KEY not set", file=sys.stderr)
        return 3

    base_url = os.environ.get("MIMO_BASE_URL", "")
    if not base_url:
        # tp- keys use Token Plan endpoint; sk- keys use pay-as-you-go endpoint
        base_url = "https://token-plan-cn.xiaomimimo.com/v1" if api_key.startswith("tp-") else "https://api.xiaomimimo.com/v1"

    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": "用自然、清晰的语气朗读以下内容。"},
            {"role": "assistant", "content": text},
        ],
        "audio": {"format": "mp3", "voice": voice},
    }
    req = urllib.request.Request(
        base_url.rstrip("/") + "/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "api-key": api_key},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"MiMo API HTTP {e.code}: {e.read().decode(errors='replace')[:500]}", file=sys.stderr)
        return 4
    except Exception as e:
        print(f"MiMo API error: {e}", file=sys.stderr)
        return 5

    try:
        audio_b64 = data["choices"][0]["message"]["audio"]["data"]
    except (KeyError, IndexError, TypeError) as e:
        print(f"unexpected MiMo response: {json.dumps(data, ensure_ascii=False)[:500]}", file=sys.stderr)
        return 6

    with open(output_path, "wb") as f:
        f.write(base64.b64decode(audio_b64))
    print(f"ok {output_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
