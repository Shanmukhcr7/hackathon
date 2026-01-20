import cv2
import google.generativeai as genai
from PIL import Image
import serial
import time
import os
import sys
import uuid
import qrcode

import firebase_admin
from firebase_admin import credentials, firestore

# ==============================
# CONFIG
# ==============================
GEMINI_API_KEY = "AIzaSyBpw9jQQgwIeSIwLBn5rNjih_R29MU3B98"
IMAGE_PATH = "captured.jpg"

ARDUINO_PORT = "COM10"
BAUD_RATE = 9600

# ==============================
# FIREBASE INIT
# ==============================
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# ==============================
# RATE PER GRAM (₹)
# ==============================
RATES = {
    "DRY": 0.02,
    "WET": 0.005
}

# ==============================
# PROMPT
# ==============================
PROMPT = """
In the given image, identify the waste category.

Dry waste categories:
- batteries
- metal
- paper
- plastic
- cardboard
- glass
- shoes
- clothes
- others

Wet waste categories:
- organic
- biological
- others

Rules:
- Choose ONLY ONE sub-category
- Choose ONLY ONE main category (dry-waste or wet-waste)
- Output format MUST be:
<subcategory>, <main-category>

Example outputs:
banana peel -> organic, wet-waste
plastic bottle -> plastic, dry-waste
"""

# ==============================
# CAMERA
# ==============================
def capture_image():
    cap = cv2.VideoCapture(1)
    if not cap.isOpened():
        cap = cv2.VideoCapture(1)

    if not cap.isOpened():
        print("❌ Camera not accessible")
        return False

    print("📸 Press SPACE to capture | ESC to cancel")

    while True:
        ret, frame = cap.read()
        cv2.imshow("Camera", frame)
        key = cv2.waitKey(1)

        if key == 27:
            cap.release()
            cv2.destroyAllWindows()
            return False

        if key == 32:
            cv2.imwrite(IMAGE_PATH, frame)
            print("✅ Image captured")
            break

    cap.release()
    cv2.destroyAllWindows()
    return True

# ==============================
# GEMINI
# ==============================
def classify_image():
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.5-flash")

    image = Image.open(IMAGE_PATH)
    response = model.generate_content([PROMPT, image])
    result = response.text.lower()

    print("🧠 Gemini output:", result)

    if "dry-waste" in result:
        return "DRY"
    elif "wet-waste" in result:
        return "WET"
    else:
        return "UNKNOWN"

# ==============================
# SERIAL HELPER
# ==============================
def wait_for_serial(prefix, ser, timeout=10):
    start = time.time()
    while True:
        if time.time() - start > timeout:
            return None

        line = ser.readline().decode(errors="ignore").strip()
        if not line:
            continue

        print("🔎 Arduino:", line)

        if line.startswith(prefix):
            return float(line.split(":")[1])

# ==============================
# MAIN
# ==============================
if __name__ == "__main__":

    print("\n🔌 Connecting to Arduino...")
    arduino = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=2)
    time.sleep(2)
    arduino.reset_input_buffer()

    # ==============================
    # 1️⃣ BASE WEIGHT
    # ==============================
    print("\n⚖️ Measuring base weight...")
    arduino.write(b"BASE\n")

    base_weight = wait_for_serial("BASE_WEIGHT", arduino, 8)
    if base_weight is None:
        print("❌ Failed to read base weight")
        arduino.close()
        sys.exit(1)

    print(f"📏 Base weight: {base_weight} g")

    # ==============================
    # 2️⃣ IMAGE CAPTURE
    # ==============================
    if not capture_image():
        arduino.close()
        sys.exit(0)

    # ==============================
    # 3️⃣ CLASSIFY
    # ==============================
    waste_type = classify_image()
    print("♻️ Waste type:", waste_type)

    if waste_type not in ["DRY", "WET"]:
        print("❌ Unable to classify waste")
        arduino.close()
        sys.exit(1)

    # ==============================
    # 4️⃣ SORT
    # ==============================
    print("🔄 Sorting waste...")
    arduino.write((waste_type + "\n").encode())

    # ==============================
    # 5️⃣ ITEM WEIGHT
    # ==============================
    item_weight = wait_for_serial("ITEM_WEIGHT", arduino, 20)
    arduino.close()

    if item_weight is None or item_weight <= 0:
        print("❌ Invalid item weight")
        sys.exit(1)

    print(f"⚖️ Item weight: {item_weight} g")

    # ==============================
    # 6️⃣ CALCULATE AMOUNT
    # ==============================
    rate = RATES[waste_type]
    amount = round(item_weight * rate, 2)

    print(f"💰 Reward amount: ₹{amount}")

    # ==============================
    # 7️⃣ GENERATE QR ID
    # ==============================
    qr_id = "QR_" + uuid.uuid4().hex[:8].upper()

    qr_data = {
        "wasteType": waste_type.lower(),
        "weight": item_weight,
        "amount": amount,
        "claimed": False,
        "claimedBy": None,
        "createdAt": firestore.SERVER_TIMESTAMP,
        "claimedAt": None
    }

    db.collection("qr_codes").document(qr_id).set(qr_data)

    print(f"🆔 QR ID: {qr_id}")

    # ==============================
    # 8️⃣ GENERATE QR CODE
    # ==============================
    qr = qrcode.QRCode(border=1)
    qr.add_data(qr_id)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img.save(f"{qr_id}.png")

    print("\n📟 Scan this QR code:\n")
    qr.print_ascii(invert=True)

    print(f"\n📁 QR image saved as {qr_id}.png")
    print("\n✅ PROCESS COMPLETE\n")
