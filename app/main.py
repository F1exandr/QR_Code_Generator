from fastapi import FastAPI, Form, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from . import models, database, auth
from .auth import verify_password, get_password_hash, create_access_token
import qrcode
import os

app = FastAPI()

# Mount static files and templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Create database tables
models.Base.metadata.create_all(bind=database.engine)

# Simple in-memory session storage (for demonstration purposes)
sessions = {}

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    username = sessions.get(request.client.host)
    return templates.TemplateResponse("index.html", {"request": request, "username": username})

@app.get("/register/", response_class=HTMLResponse)
async def get_register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register/")
async def register(username: str = Form(...), password: str = Form(...), db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.username == username).first()
    if user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = get_password_hash(password)
    new_user = models.User(username=username, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    # Redirect to the main page after successful registration
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/login/", response_class=HTMLResponse)
async def get_login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db), request: Request = None):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user.username})
    # Store session
    sessions[request.client.host] = user.username
    # Redirect to the main page
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    return response

@app.get("/logout/")
async def logout(request: Request):
    # Clear session
    sessions.pop(request.client.host, None)
    # Redirect to the main page
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/generate/")
async def generate_qr(text: str = Form(...)):
    img = qrcode.make(text)
    img_path = "app/static/qr.png"
    img.save(img_path)
    return {"qr_path": "static/qr.png"}