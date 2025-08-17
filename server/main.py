import os
import cv2
import re
import pytesseract
from flask import Flask, request, jsonify
from flask_cors import CORS
from inference_sdk import InferenceHTTPClient
import firebase_admin
from firebase_admin import credentials, firestore
import base64
import json
from datetime import datetime

# --------------------
# Firebase Init
# --------------------
service_account_b64 = os.getenv("SERVICE_ACCOUNT_KEY_BASE64")
if service_account_b64:
    service_account_json = base64.b64decode(service_account_b64).decode("utf-8")
    cred = credentials.Certificate(json.loads(service_account_json))
    firebase_admin.initialize_app(cred)
    db = firestore.client()
else:
    db = None

# --------------------
# Roboflow Client
# --------------------
ROBOFLOW_API_KEY = os.getenv("ROBOFLOW_API_KEY")
client = InferenceHTTPClient(api_key=ROBOFLOW_API_KEY)

DETECT_MODEL_ID = "number_plate_detection-v3zjj/3"
OCR_MODEL_ID = "license-ocr-qqq6v/3"

# --------------------
# Flask App
# --------------------
app = Flask(__name__)
CORS(app)

# --------------------
# Helpers
# --------------------
def resize_image(image_path, max_size=1024):
    img = cv2.imread(image_path)
    h, w = img.shape[:2]
    scale = max_size / max(h, w)
    if scale < 1:
        img = cv2.resize(img, (int(w*scale), int(h*scale)))
        cv2.imwrite(image_path, img)
    return image_path

def clean_text(text: str):
    return re.sub(r'[^A-Z0-9]', '', text.upper()).strip()

def ocr_with_tesseract(crop_path):
    img = cv2.imread(crop_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    gray = cv2.bilateralFilter(gray, 9, 75, 75)
    _, th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    config = '-c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 --psm 7'
    text = pytesseract.image_to_string(th, config=config)
    return clean_text(text)

def ocr_with_roboflow(crop_path):
    try:
        result = client.infer(crop_path, model_id=OCR_MODEL_ID)
        if "predictions" not in result:
            return ""
        preds = result["predictions"]
        if not preds:
            return ""
        # sort predictions left-to-right
        preds = sorted(preds, key=lambda p: p["x"])
        chars = [p["class"] for p in preds]
        return clean_text("".join(chars))
    except Exception as e:
        print("Roboflow OCR error:", e)
        return ""

# --------------------
# Route
# --------------------
@app.route("/api/recognize-plate", methods=["POST"])
def recognize_plate():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files["file"]
    os.makedirs("images", exist_ok=True)
    save_path = os.path.join("images", file.filename)
    file.save(save_path)
    resize_image(save_path)

    try:
        detection_result = client.infer(save_path, model_id=DETECT_MODEL_ID)
    except Exception as e:
        return jsonify({"error": f"Roboflow detection failed: {e}"}), 500

    if "predictions" not in detection_result:
        return jsonify({"plates": []})

    results = []
    img = cv2.imread(save_path)
    h, w = img.shape[:2]

    for i, det in enumerate(detection_result["predictions"]):
        x, y, bw, bh = det["x"], det["y"], det["width"], det["height"]
        x1, y1 = max(int(x - bw/2), 0), max(int(y - bh/2), 0)
        x2, y2 = min(int(x + bw/2), w), min(int(y + bh/2), h)
        plate_crop = img[y1:y2, x1:x2]

        crop_path = f"images/crop_{i}.jpg"
        cv2.imwrite(crop_path, plate_crop)

        # OCR pipeline: Tesseract → fallback Roboflow
        text = ocr_with_tesseract(crop_path)
        if len(text) < 4:  # too short, likely failed
            text = ocr_with_roboflow(crop_path)

        plate_info = {
            "recognized_text": text,
            "bbox": [x1, y1, x2, y2],
            "timestamp": datetime.utcnow().isoformat()
        }

        if db and text:
            doc_ref = db.collection("vehicles").document(text)
            doc = doc_ref.get()
            if doc.exists:
                plate_info["known"] = True
                plate_info["owner"] = doc.to_dict()
            else:
                plate_info["known"] = False

        results.append(plate_info)

    return jsonify({"plates": results})

# --------------------
# Main
# --------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
