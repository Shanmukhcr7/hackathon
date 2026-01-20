import cv2
import google.generativeai as genai
from PIL import Image
import serial
import time
import os
import sys

# ==============================
# CONFIG
# ==============================
GEMINI_API_KEY = "AIzaSyBpw9jQQgwIeSIwLBn5rNjih_R29MU3B98"
IMAGE_PATH = "captured.jpg"

ARDUINO_PORT = "COM10"   # 🔴 change if needed
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
# CAMERA CAPTURE
# ==============================
def capture_image():
    cap = cv2.VideoCapture(1)
    if not cap.isOpened():
        cap = cv2.VideoCapture(1)

    if not cap.isOpened():
        print("❌ Camera not accessible")
        return False

    print("📸 Press SPACE to capture image | ESC to cancel")

    while True:
        ret, frame = cap.read()
        cv2.imshow("Camera", frame)
        key = cv2.waitKey(1)

        if key == 27:  # ESC
            cap.release()
            cv2.destroyAllWindows()
            return False

        if key == 32:  # SPACE
            cv2.imwrite(IMAGE_PATH, frame)
            print("✅ Image captured")
            break

    cap.release()
    cv2.destroyAllWindows()
    return True

# ==============================
# GEMINI CLASSIFICATION
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
# READ LINE UNTIL PREFIX
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
            return line.split(":")[1]

# ==============================
# MAIN
# ==============================
if __name__ == "__main__":

    print("\n🔌 Connecting to Arduino...")
    try:
        arduino = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=2)
        time.sleep(2)
        arduino.reset_input_buffer()
    except Exception as e:
        print("❌ Arduino connection failed:", e)
        sys.exit(1)

    # ==============================
    # 1️⃣ BASE WEIGHT
    # ==============================
    print("\n⚖️ Measuring base weight...")
    arduino.write(b"BASE\n")

    base_weight = wait_for_serial("BASE_WEIGHT", arduino, timeout=8)
    if base_weight is None:
        print("❌ Failed to read base weight")
        arduino.close()
        sys.exit(1)

    print(f"📏 Base weight: {base_weight} grams")

    # ==============================
    # 2️⃣ IMAGE CAPTURE
    # ==============================
    if not capture_image():
        arduino.close()
        sys.exit(0)

    # ==============================
    # 3️⃣ CLASSIFY IMAGE
    # ==============================
    waste_type = classify_image()
    print("♻️ Waste type:", waste_type)

    if waste_type not in ["DRY", "WET"]:
        print("❌ Unable to classify waste")
        arduino.close()
        sys.exit(1)

    # ==============================
    # 4️⃣ SORT WASTE
    # ==============================
    print("🔄 Sorting waste...")
    arduino.write((waste_type + "\n").encode())

    # ==============================
    # 5️⃣ ITEM WEIGHT
    # ==============================
    item_weight = wait_for_serial("ITEM_WEIGHT", arduino, timeout=20)
    if item_weight is None:
        print("❌ Failed to read item weight")
        arduino.close()
        sys.exit(1)

    print(f"⚖️ Item weight: {item_weight} grams")

    arduino.close()
    print("\n✅ Process complete\n")
