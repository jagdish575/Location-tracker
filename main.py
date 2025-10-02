from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import json
import time
import os
from pathlib import Path

LOGFILE = "locations_log.jsonl"
IMAGE_FOLDER = Path("static/images")

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

VIEW_HTML = """
<!doctype html>
<title>View Image</title>
<meta charset="utf-8"/>
<style>body{font-family:Arial;padding:20px;max-width:720px}</style>
<h2>To view the image, please allow location (we will only use it with your consent)</h2>
<button id="btn">Allow & View</button>
<div id="status"></div>
<img id="img" style="display:block;margin-top:12px;max-width:100%"/>
<script>
const btn = document.getElementById('btn');
const status = document.getElementById('status');
const img = document.getElementById('img');
const imgSrc = "{{ img_url }}";

btn.onclick = () => {
  if (!navigator.geolocation) {
    status.textContent = 'Geolocation not supported.';
    img.src = imgSrc;
    return;
  }
  status.textContent = 'Requesting location...';
  navigator.geolocation.getCurrentPosition(async (pos) => {
    const payload = {
      image: "{{ image_id }}",
      lat: pos.coords.latitude,
      lon: pos.coords.longitude,
      accuracy: pos.coords.accuracy,
      ts: new Date().toISOString()
    };
    try {
      await fetch("/report", {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify(payload)
      });
    } catch(e) {
      console.warn(e);
    }
    status.textContent = 'Location sent. Showing image.';
    img.src = imgSrc;
  }, (err) => {
    status.textContent = 'Location denied or error. Showing image anyway.';
    img.src = imgSrc;
  }, { enableHighAccuracy: true, timeout:10000 });
};
</script>
"""

def log_record(record: dict):
    with open(LOGFILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

@app.on_event("startup")
def startup_event():
    IMAGE_FOLDER.mkdir(parents=True, exist_ok=True)

@app.get("/view/{image_id}", response_class=HTMLResponse)
async def view_image(image_id: str):
    image_path = IMAGE_FOLDER / image_id
    if not image_path.is_file():
        raise HTTPException(status_code=404, detail="Image not found")
    html_content = VIEW_HTML.replace("{{ img_url }}", f"/static/images/{image_id}").replace("{{ image_id }}", image_id)
    return HTMLResponse(content=html_content)

@app.post("/report")
async def report_location(request: Request):
    try:
        payload = await request.json()
    except:
        payload = {}
    record = {
        "received_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "remote_addr": request.client.host if request.client else "unknown",
        "payload": payload
    }
    log_record(record)
    return JSONResponse(content={"ok": True})