#!/usr/bin/env python3
"""MiMo V2.5 TTS voicedesign/voiceclone bridge for Hermes.

Usage:
  mimo-voice.py <model> <style_prompt_or_path> <text> <output> [format]
    model: mimo-v2.5-tts-voicedesign | mimo-v2.5-tts-voiceclone
    for voicedesign: <style_prompt_or_path> = inline text description (in quotes)
    for voiceclone:  <style_prompt_or_path> = path to reference audio (mp3/wav)
"""
import base64, json, os, sys, urllib.request

def main():
    if len(sys.argv) < 5:
        print("usage: mimo-voice.py <model> <style|audio_path> <text> <output> [fmt]", file=sys.stderr)
        return 2
    model = sys.argv[1]
    style_or_audio = sys.argv[2]
    text = sys.argv[3]
    output = sys.argv[4]
    fmt = sys.argv[5] if len(sys.argv) > 5 else "mp3"

    api_key = os.environ.get("MIMO_API_KEY") or os.environ.get("MIMO_METERED_API_KEY") or ""
    if not api_key:
        print("MIMO_API_KEY not set", file=sys.stderr); return 3
    base_url = os.environ.get("MIMO_BASE_URL", "")
    if not base_url:
        base_url = "https://token-plan-cn.xiaomimimo.com/v1" if api_key.startswith("tp-") else "https://api.xiaomimimo.com/v1"

    # voice field
    voice = None
    user_content = ""
    if model.endswith("voiceclone"):
        with open(style_or_audio, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        mime = "audio/mpeg" if style_or_audio.lower().endswith(".mp3") else "audio/wav"
        voice = f"data:{mime};base64,{b64}"
    else:  # voicedesign
        user_content = style_or_audio

    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": user_content},
            {"role": "assistant", "content": text},
        ],
        "audio": {"format": fmt, "optimize_text_preview": False},
    }
    if voice:
        payload["audio"]["voice"] = voice

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
        print(f"HTTP {e.code}: {e.read().decode(errors='replace')[:400]}", file=sys.stderr); return 4
    except Exception as e:
        print(f"err: {e}", file=sys.stderr); return 5
    try:
        audio_b64 = data["choices"][0]["message"]["audio"]["data"]
    except (KeyError, IndexError, TypeError) as e:
        print(f"unexpected resp: {json.dumps(data, ensure_ascii=False)[:400]}", file=sys.stderr); return 6
    with open(output, "wb") as f:
        f.write(base64.b64decode(audio_b64))
    print(f"ok {output}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
