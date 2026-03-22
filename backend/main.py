import os
import shutil
import asyncio
from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

# Import the existing tools
from downloader import download_music
from utils import search_youtube, convert_audio, write_metadata
from enhancer import enhance_audio
from history_manager import HistoryManager

app = FastAPI(title="MusicPro Web API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("downloads", exist_ok=True)
os.makedirs("uploads", exist_ok=True)
os.makedirs("enhanced", exist_ok=True)

history_manager = HistoryManager()

# Data Models
class SearchRequest(BaseModel):
    query: str
    limit: int = 15

class DownloadRequest(BaseModel):
    url: str
    format: str = "mp3"
    preset: str = "Smart (Auto)"

@app.get("/")
def root():
    return {"status": "ok", "message": "MusicPro API is running"}

@app.post("/api/search")
async def search(req: SearchRequest):
    results = await asyncio.to_thread(search_youtube, req.query, limit=req.limit)
    return {"results": results}

@app.post("/api/download")
async def download(req: DownloadRequest):
    try:
        # Run the yt-dlp download in a separate thread to prevent blocking
        # Note: We aren't using status hooks via websocket yet, but standard wait is fine for now
        downloaded_items = await asyncio.to_thread(
            download_music, req.url, None, req.format, req.preset
        )
        if downloaded_items:
            for item in downloaded_items:
                history_manager.add_entry(item['title'], item['artist'], item['file_path'], item['format'])
            return {"status": "success", "items": downloaded_items}
        else:
            return JSONResponse(status_code=400, content={"status": "error", "message": "Download failed"})
    except Exception as e:
         return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

@app.get("/api/history")
def get_history():
    history_manager.load()
    return {"history": history_manager.get_all()}

@app.post("/api/convert")
async def convert(background_tasks: BackgroundTasks, file: UploadFile = File(...), target_format: str = Form("mp3")):
    upload_path = os.path.join("uploads", file.filename)
    with open(upload_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    ok, msg, out_path = await asyncio.to_thread(convert_audio, upload_path, target_format)
    
    # Cleanup original upload
    background_tasks.add_task(os.remove, upload_path)
    
    if ok and out_path and os.path.exists(out_path):
        # We can return the file directly and delete it afterwards
        background_tasks.add_task(os.remove, out_path)
        return FileResponse(out_path, filename=os.path.basename(out_path))
    else:
        return JSONResponse(status_code=400, content={"status": "error", "message": msg})

@app.post("/api/metadata")
async def update_metadata(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    artist: Optional[str] = Form(None),
    album: Optional[str] = Form(None)
):
    upload_path = os.path.join("uploads", file.filename)
    with open(upload_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    ok, msg = await asyncio.to_thread(write_metadata, upload_path, title, artist, album)
    
    if ok:
        background_tasks.add_task(os.remove, upload_path)
        return FileResponse(upload_path, filename=file.filename)
    else:
        background_tasks.add_task(os.remove, upload_path)
        return JSONResponse(status_code=400, content={"status": "error", "message": msg})

@app.post("/api/remaster")
async def handle_remaster(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    preset: str = Form("Smart (Auto)")
):
    upload_path = os.path.join("uploads", file.filename)
    out_path = os.path.join("enhanced", f"remastered_{file.filename}")
    
    with open(upload_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    from utils import get_audio_bitrate
    bitrate = await asyncio.to_thread(get_audio_bitrate, upload_path)
    is_low = (bitrate and bitrate < 128)
    
    ok = await asyncio.to_thread(enhance_audio, upload_path, out_path, is_low, preset)
    
    background_tasks.add_task(os.remove, upload_path)
    
    if ok and os.path.exists(out_path):
        background_tasks.add_task(os.remove, out_path)
        return FileResponse(out_path, filename=os.path.basename(out_path))
    else:
        return JSONResponse(status_code=500, content={"status": "error", "message": "Remastering failed"})

# Mount static files to serve the downloads
from fastapi.staticfiles import StaticFiles
app.mount("/downloads", StaticFiles(directory="downloads"), name="downloads")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
