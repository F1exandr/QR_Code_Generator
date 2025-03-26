from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import qrcode
import os

app = FastAPI()

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return templates.TemplateResponse("index.html", {"request": {}})

@app.post("/generate/")
async def generate_qr(text: str = Form(...)):
    img = qrcode.make(text)
    img_path = "app/static/qr.png"
    img.save(img_path)
    return {"qr_path": img_path}

@app.get("/download/")
async def download_qr():
    return FileResponse("app/static/qr.png", media_type='application/octet-stream', filename="qr.png")