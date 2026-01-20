import cv2
import google.generativeai as genai
from PIL import Image
import serial
import time
import os

# ==============================
# CONFIG
# ==============================
GEMINI_API_KEY = "AIzaSyBpw9jQQgwIeSIwLBn5rNjih_R29MU3B98"   # 🔴 move to env later
IMAGE_PATH = "captured.jpg"

ARDUINO_PORT = "COM10"
BAUD_RATE = 9600

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
# MAIN
# ==============================
if __name__ == "__main__":

    # 🔹 Connect to Arduino
    arduino = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=2)
    time.sleep(2)
    arduino.reset_input_buffer()

    # ==============================
    # 1️⃣ MEASURE BASE WEIGHT
    # ==============================
    print("⚖️ Measuring base weight...")
    arduino.write(b"BASE\n")

    base_weight = None
    start_time = time.time()

    while True:
        if time.time() - start_time > 8:
            print("⏰ Failed to read base weight")
            arduino.close()
            exit()

        line = arduino.readline().decode(errors="ignore").strip()
        if not line:
            continue

        print("🔎 Arduino:", line)

        if line.startswith("BASE_WEIGHT"):
            base_weight = line.split(":")[1]
            print(f"📏 Base weight: {base_weight} grams")
            break

    # ==============================
    # 2️⃣ CAPTURE IMAGE
    # ==============================
    if not capture_image():
        arduino.close()
        exit()

    # ==============================
    # 3️⃣ CLASSIFY WASTE
    # ==============================
    waste_type = classify_image()
    print("♻️ Waste type:", waste_type)

    if waste_type not in ["DRY", "WET"]:
        print("❌ Unable to classify waste")
        arduino.close()
        exit()

    # ==============================
    # 4️⃣ SORT WASTE
    # ==============================
    print("🔄 Sorting waste...")
    arduino.write((waste_type + "\n").encode())

    # ==============================
    # 5️⃣ READ ITEM WEIGHT
    # ==============================
    start_time = time.time()
    timeout = 15

    while True:
        if time.time() - start_time > timeout:
            print("⏰ Timeout waiting for item weight")
            break

        line = arduino.readline().decode(errors="ignore").strip()
        if line.startswith("ITEM_WEIGHT"):
            item_weight = line.split(":")[1]
            print(f"⚖️ Item weight: {item_weight} grams")
            break

    arduino.close()
