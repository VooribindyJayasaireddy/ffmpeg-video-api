from flask import Flask, request, send_file, jsonify
import os, subprocess, requests, shutil

app = Flask(__name__)

@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok"}

@app.route("/render", methods=["POST"])
def render_video():
    try:
        data = request.json

        slides = data["slides"]
        audio_url = data["audio_url"]

        # clean workspace
        if os.path.exists("work"):
            shutil.rmtree("work")
        os.makedirs("work/slides", exist_ok=True)

        # download slides as 000.png, 001.png ...
        for i, url in enumerate(slides):
            r = requests.get(url, allow_redirects=True, timeout=30)
            if r.status_code != 200:
                return jsonify({"error": f"Failed to download slide {i}"}), 400
            with open(f"work/slides/{i:03d}.png", "wb") as f:
                f.write(r.content)

        # download audio
        audio = requests.get(audio_url, allow_redirects=True, timeout=30)
        if audio.status_code != 200:
            return jsonify({"error": "Failed to download audio"}), 400

        with open("work/audio.mp3", "wb") as f:
            f.write(audio.content)

        # FFmpeg command (robust)
        cmd = [
            "ffmpeg",
            "-y",
            "-framerate", "1",
            "-i", "work/slides/%03d.png",
            "-i", "work/audio.mp3",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-shortest",
            "-movflags", "+faststart",
            "work/output.mp4"
        ]

        subprocess.run(cmd, check=True)

        return send_file("work/output.mp4", mimetype="video/mp4")

    except subprocess.CalledProcessError as e:
        return jsonify({"error": "FFmpeg failed", "details": str(e)}), 500
    except Exception as e:
        return jsonify({"error": "Server error", "details": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
