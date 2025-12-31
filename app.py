from flask import Flask, request, send_file
import os, subprocess, requests
import base64
app = Flask(__name__)

@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok"}

@app.route("/render", methods=["POST"])
def render_video():
    data = request.json
    slides = data["slides"]
    audio_url = data["audio_url"]

    os.makedirs("slides", exist_ok=True)

    # download slides
    for i, url in enumerate(slides):
        r = requests.get(url)
        with open(f"slides/{i}.png", "wb") as f:
            f.write(r.content)

    # download audio
    audio_base64 = data["audio_base64"]
    audio_bytes = base64.b64decode(audio_base64)

    with open("audio.mp3", "wb") as f:
        f.write(audio_bytes)

    # create video
    subprocess.run([
        "ffmpeg", "-y",
        "-framerate", "1",
        "-i", "slides/%d.png",
        "-i", "audio.mp3",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-shortest",
        "output.mp4"
    ], check=True)

    return send_file("output.mp4", mimetype="video/mp4")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
