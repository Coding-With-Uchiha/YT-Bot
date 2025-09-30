from flask import Flask, render_template, request, send_file
import yt_dlp
from io import BytesIO
import os

app = Flask(__name__)

COOKIE_FILE = "cookies.txt"  # optional for private Instagram

def get_formats(url):
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
    }
    if os.path.exists(COOKIE_FILE):
        ydl_opts["cookiefile"] = COOKIE_FILE

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        formats = [
            {"format_id": f["format_id"], "resolution": f.get("resolution") or f.get("height"), "ext": f["ext"]}
            for f in info.get("formats", [])
            if f.get("vcodec") != "none"
        ]
        title = info.get("title", "video")
    return formats, title

def download_video(url, format_id):
    buffer = BytesIO()
    ydl_opts = {
        "format": format_id,
        "outtmpl": "video.mp4",
    }
    if os.path.exists(COOKIE_FILE):
        ydl_opts["cookiefile"] = COOKIE_FILE

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    with open("video.mp4", "rb") as f:
        buffer.write(f.read())
    os.remove("video.mp4")
    buffer.seek(0)
    return buffer

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        url = request.form["url"]
        format_id = request.form.get("format_id")

        if not format_id:
            try:
                formats, title = get_formats(url)
                return render_template("index.html", formats=formats, url=url, title=title)
            except Exception as e:
                return f"Error fetching formats: {e}"
        else:
            try:
                buffer = download_video(url, format_id)
                return send_file(buffer, as_attachment=True, download_name="video.mp4", mimetype="video/mp4")
            except Exception as e:
                return f"Error downloading video: {e}"

    return render_template("index.html", formats=None)

if __name__ == "__main__":
    import os
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
