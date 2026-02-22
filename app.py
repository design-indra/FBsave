from flask import Flask, render_template, request, redirect, Response
import requests
import os
import time
import re

template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=template_dir)

RAPIDAPI_KEY = "f30b4baaecmsh7d04f39e3f19019p15339bjsnad800cd8c0d2"
RAPIDAPI_HOST = "facebook-video-and-reel-downloader.p.rapidapi.com"

def clean_fb_url(url):
    url = url.strip()
    if "facebook.com" in url or "fb.com" in url or "fb.watch" in url:
        return url
    return None

def get_fb_data(url):
    clean_url = clean_fb_url(url)
    if not clean_url:
        return None

    print(f"Fetching FB: {clean_url}")

    try:
        r = requests.post(
            f"https://{RAPIDAPI_HOST}/app/main.php",
            data={"url": clean_url},
            headers={
                "x-rapidapi-key": RAPIDAPI_KEY,
                "x-rapidapi-host": RAPIDAPI_HOST,
                "Content-Type": "application/x-www-form-urlencoded"
            },
            timeout=20
        )
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text[:500]}")

        data = r.json()

        # Cari video URL di berbagai struktur response
        hd_url = None
        sd_url = None
        title = data.get("title", "Facebook Video")
        thumbnail = data.get("thumbnail", "")

        if data.get("hd"):
            hd_url = data["hd"]
        if data.get("sd"):
            sd_url = data["sd"]

        # Struktur alternatif
        if not hd_url and not sd_url:
            links = data.get("links") or data.get("videos") or []
            for item in links:
                q = item.get("quality", "").lower()
                u = item.get("url") or item.get("link", "")
                if "hd" in q:
                    hd_url = u
                elif "sd" in q or "low" in q:
                    sd_url = u

        if hd_url or sd_url:
            return {
                "title": title,
                "thumbnail": thumbnail,
                "hd": hd_url,
                "sd": sd_url
            }

    except Exception as e:
        print(f"FB error: {e}")

    return None

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    error = None
    if request.method == "POST":
        input_url = request.form.get("url", "").strip()
        if not input_url or ("facebook.com" not in input_url and "fb.com" not in input_url and "fb.watch" not in input_url):
            error = "Masukkan link video Facebook yang valid."
        else:
            result = get_fb_data(input_url)
            if not result:
                error = "Gagal mengambil video. Pastikan link benar dan video tidak diprivat."
    return render_template("index.html", result=result, error=error)

@app.route("/download")
def download():
    video_url = request.args.get("url")
    quality = request.args.get("q", "sd")
    if not video_url:
        return "URL tidak valid", 400
    try:
        r = requests.get(
            video_url,
            headers={"User-Agent": "Mozilla/5.0", "Referer": "https://www.facebook.com/"},
            stream=True,
            timeout=25
        )
        filename = f"FBSave_{quality}_{int(time.time())}.mp4"
        def generate():
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    yield chunk
        return Response(generate(), headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": "video/mp4",
        })
    except Exception as e:
        print(f"Download error: {e}")
        return redirect(video_url)

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/privacy")
def privacy():
    return render_template("privacy.html")

if __name__ == "__main__":
    app.run(debug=True)
