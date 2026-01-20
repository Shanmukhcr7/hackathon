import cv2
import google.generativeai as genai
from PIL import Image
import serial
import time
import os

# ==============================
# CONFIG
# ==============================
GEMINI_API_KEY = "AIzaSyBpw9jQQgwIeSIwLBn5rNjih_R29MU3B98"

IMAGE_PATH = "captured.jpg"
ARDUINO_PORT = "COM9"      # 🔴 CHANGE IF NEEDED
BAUD_RATE = 9600

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
        print("❌ Camera not accessible")
        return False

    print("📸 Press SPACE to capture image | ESC to cancel")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        cv2.imshow("Camera", frame)
        key = cv2.waitKey(1)

        if key == 27:  # ESC
            cap.release()
            cv2.destroyAllWindows()
            return False

        elif key == 32:  # SPACE
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

    response = model.generate_content(
        [PROMPT, image],
        generation_config={"temperature": 0.1}
    )

    result = response.text.strip().lower()

    print("\n♻️ Waste Classification Result:")
    print(result)

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

    if not capture_image():
        exit()

    waste_type = classify_image()

    try:
        arduino = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=1)
        time.sleep(2)  # wait for Arduino reset

        if waste_type == "DRY":
            print("🟢 DRY waste detected → rotating servo LEFT")
            arduino.write(b"DRY\n")

        elif waste_type == "WET":
            print("🔵 WET waste detected → rotating servo RIGHT")
            arduino.write(b"WET\n")

        else:
            print("❌ Unable to classify waste")
            arduino.close()
            exit()

        print("\n▶️ Servo active")
        print("Press 'q' + ENTER to stop")

        while True:
            key = input()
            if key.lower() == 'q':
                print("🛑 Stopping servo")
                break

        arduino.write(b"NONE\n")
        arduino.close()

    except Exception as e:
        print("❌ Arduino communication error:", e)
