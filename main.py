import cv2
import google.generativeai as genai
from PIL import Image
import serial
import time
import os
import uuid
import qrcode
import base64
import threading
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import firebase_admin
from firebase_admin import credentials, firestore

# ==============================
# CONFIG & INITIALIZATION
# ==============================
app = FastAPI()

# Enable CORS for the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

GEMINI_API_KEY = "AIzaSyBpw9jQQgwIeSIwLBn5rNjih_R29MU3B98"
IMAGE_PATH = "captured.jpg"
ARDUINO_PORT = "COM10"
BAUD_RATE = 9600

# Firebase Init
try:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)
    db = firestore.client()
except Exception as e:
    print(f"⚠️ Firebase warning: {e}. Ensure serviceAccountKey.json exists.")

# Serial Init
arduino = None
try:
    arduino = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=2)
    time.sleep(2)
    arduino.reset_input_buffer()
    print(f"✅ Connected to Arduino on {ARDUINO_PORT}")
except Exception as e:
    print(f"❌ Arduino connection failed: {e}")

RATES = {"DRY": 0.02, "WET": 0.005}

# ==============================
# UTILS
# ==============================

def wait_for_serial(prefix, timeout=15):
    if not arduino: return None
    start = time.time()
    while True:
        if time.time() - start > timeout:
            return None
        line = arduino.readline().decode(errors="ignore").strip()
        if line.startswith(prefix):
            try:
                return float(line.split(":")[1])
            except:
                return None

# ==============================
# API ENDPOINTS
# ==============================

@app.get("/status")
async def get_status():
    return {
        "arduino_connected": arduino is not None,
        "camera_available": cv2.VideoCapture(0).isOpened()
    }

@app.post("/measure-base")
async def measure_base():
    if not arduino:
        raise HTTPException(status_code=500, detail="Arduino not connected")
    
    arduino.write(b"BASE\n")
    val = wait_for_serial("BASE_WEIGHT")
    if val is None:
        raise HTTPException(status_code=500, detail="Failed to read base weight")
    return {"weight": val}

@app.post("/capture")
async def capture():
    cap = cv2.VideoCapture(1) # Adjust index if needed
    ret, frame = cap.read()
    if not ret:
        cap.release()
        raise HTTPException(status_code=500, detail="Camera capture failed")
    
    cv2.imwrite(IMAGE_PATH, frame)
    _, buffer = cv2.imencode('.jpg', frame)
    img_str = base64.b64encode(buffer).decode('utf-8')
    cap.release()
    return {"image": img_str}

@app.post("/classify")
async def classify():
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.5-flash") # Use stable model

    prompt = """
    Identify waste category. Dry categories: batteries, metal, paper, plastic, cardboard, glass, shoes, clothes. 
    Wet categories: organic, biological.
    Format: <subcategory>, <main-category> (dry-waste or wet-waste)
    """
    
    image = Image.open(IMAGE_PATH)
    response = model.generate_content([prompt, image])
    result = response.text.lower()
    
    waste_type = "UNKNOWN"
    if "dry-waste" in result:
        waste_type = "DRY"
    elif "wet-waste" in result:
        waste_type = "WET"
        
    return {"category": result.strip(), "type": waste_type}

@app.post("/process-waste")
async def process_waste(payload: dict):
    waste_type = payload.get("type")
    if not arduino:
        raise HTTPException(status_code=500, detail="Arduino not connected")
    
    # Sort
    arduino.write((waste_type + "\n").encode())
    
    # Get Weight
    item_weight = wait_for_serial("ITEM_WEIGHT", timeout=25)
    if item_weight is None:
        raise HTTPException(status_code=500, detail="Scale timeout")
    
    # Calculate
    amount = round(item_weight * RATES.get(waste_type, 0), 2)
    
    # Firebase & QR
    qr_id = "QR_" + uuid.uuid4().hex[:8].upper()
    qr_data = {
        "wasteType": waste_type.lower(),
        "weight": item_weight,
        "amount": amount,
        "claimed": False,
        "createdAt": firestore.SERVER_TIMESTAMP
    }
    
    try:
        db.collection("qr_codes").document(qr_id).set(qr_data)
    except:
        print("Firebase offline, skipping DB write")

    # Generate QR Image for UI
    qr = qrcode.QRCode(border=1)
    qr.add_data(qr_id)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(f"static_qr.png")
    
    with open("static_qr.png", "rb") as f:
        qr_base64 = base64.b64encode(f.read()).decode()

    return {
        "id": qr_id,
        "weight": item_weight,
        "amount": amount,
        "qr_code": qr_base64
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)