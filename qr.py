import firebase_admin
from firebase_admin import credentials, firestore
import qrcode
import uuid

# ==============================
# FIREBASE INITIALIZATION
# ==============================
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

# ==============================
# MANUAL INPUT (TEST MODE)
# ==============================
waste_type = input("Enter waste type (dry/wet): ").strip().lower()
weight = float(input("Enter weight (grams): ").strip())

# ==============================
# RATE LOGIC
# ==============================
rates = {
    "dry": 0.02,
    "wet": 0.005
}

if waste_type not in rates:
    print("❌ Invalid waste type")
    exit()

amount = round(weight * rates[waste_type], 2)

# ==============================
# GENERATE QR ID
# ==============================
qr_id = "QR_" + uuid.uuid4().hex[:8].upper()

# ==============================
# WRITE TO FIREBASE
# ==============================
qr_data = {
    "amount": amount,
    "wasteType": waste_type,
    "claimed": False,
    "claimedBy": None,
    "createdAt": firestore.SERVER_TIMESTAMP,
    "claimedAt": None
}

db.collection("qr_codes").document(qr_id).set(qr_data)

print("\n✅ QR Code created successfully")
print(f"🆔 QR ID  : {qr_id}")
print(f"💰 Amount: ₹{amount}")

# ==============================
# GENERATE QR CODE (IMAGE + TERMINAL)
# ==============================
qr = qrcode.QRCode(border=1)
qr.add_data(qr_id)
qr.make(fit=True)

# Save image
img = qr.make_image(fill_color="black", back_color="white")
img.save(f"{qr_id}.png")

# Print QR in terminal
print("\n📟 Scan this QR code (terminal view):\n")
qr.print_ascii(invert=True)

print(f"\n📁 QR image saved as: {qr_id}.png")
