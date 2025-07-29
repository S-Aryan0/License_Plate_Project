import os
import cv2
import uuid
from inference_sdk import InferenceHTTPClient
from firebase_config import db
from flask import Flask, request, jsonify
from flask_cors import CORS

# Flask App Initialization
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Load Roboflow API Key from environment
API_KEY = os.getenv("ROBOFLOW_API_KEY")
if not API_KEY:
    print("❌ API key is missing! Set it in the Render environment.")

# Initialize Roboflow Client
client = InferenceHTTPClient(
    api_url="https://detect.roboflow.com",
    api_key=API_KEY
)


# Model IDs
MODEL_ID = "number_plate_detection-v3zjj/3"
MODEL_ID1 = "license-ocr-qqq6v/3"

# Ensure images directory exists
os.makedirs("images", exist_ok=True)

# Resize Image Function
def resize_image(image_path, max_size=1024):
    img = cv2.imread(image_path)
    if img is None:
        print("❌ Failed to load image!")
        return None
    
    h, w = img.shape[:2]
    if max(h, w) > max_size:
        scale = max_size / max(h, w)
        new_size = (int(w * scale), int(h * scale))
        img = cv2.resize(img, new_size, interpolation=cv2.INTER_AREA)
        resized_path = os.path.join("images", "resized_" + os.path.basename(image_path))
        cv2.imwrite(resized_path, img)
        print(f"✅ Resized image saved at {resized_path}")
        return resized_path
    return image_path

# License Plate Recognition Route
@app.route('/api/recognize-plate', methods=['POST'])
def recognize_plate():
    if 'image' not in request.files:
        return jsonify({"error": "No image provided"}), 400
    
    file = request.files['image']
    unique_filename = f"{uuid.uuid4()}.jpg"
    image_path = os.path.join("images", unique_filename)
    file.save(image_path)

    # Resize and check image
    image_path = resize_image(image_path)
    if image_path is None:
        return jsonify({"error": "Failed to process image"}), 500
    
    print(f"✅ Processing image: {image_path}")

    # Run License Plate Detection
    result = client.infer(image_path, model_id=MODEL_ID)
    print("🚗 License Plate Detection Result:", result)

    if 'predictions' not in result or not result['predictions']:
        return jsonify({"error": "No license plate detected"}), 400
    
    response_data = {"plates": []}
    image = cv2.imread(image_path)

    for prediction in result['predictions']:
        x, y, width, height = map(int, [prediction['x'], prediction['y'], prediction['width'], prediction['height']])
        license_plate_crop = image[y - height//2:y + height//2, x - width//2:x + width//2]

        output_cropped_path = "images/cropped_plate.jpg"
        cv2.imwrite(output_cropped_path, license_plate_crop)
        print(f"🖼️ Cropped plate saved at {output_cropped_path}")

        # Run OCR
        result1 = client.infer(output_cropped_path, model_id=MODEL_ID1)
        print("🔠 OCR Response:", result1)

        if 'predictions' not in result1 or not result1['predictions']:
            print("❌ OCR failed to recognize characters")
            continue

        # Sort OCR predictions and extract text
        result1['predictions'] = sorted(result1['predictions'], key=lambda x: (x['y'], -x['x']))
        recognized_text = "".join([pred['class'] for pred in result1['predictions']])

        if len(recognized_text) < 10:
            print("⚠️ OCR output is too short:", recognized_text)
            continue
        
        # Fix reversed text
        if recognized_text[0].isdigit() and recognized_text[1].isdigit():
            recognized_text = recognized_text[::-1]
        elif recognized_text[0].isalpha() and recognized_text[1].isdigit():
            recognized_text = recognized_text[:5][::-1] + recognized_text[5:][::-1]

        print(f"✅ Recognized License Plate: {recognized_text}")

        # Fetch owner details from Firebase
        plate_info = {
            "text": recognized_text,
            "known": False,
            "owner": None,
            "roll_number": None
        }

        # Reference the document for the recognized license plate
        doc_ref = db.collection('vehicles').document(recognized_text)
        doc = doc_ref.get()

        if doc.exists:
            vehicle_data = doc.to_dict()
            plate_info.update({
                "known": True,
                "owner": vehicle_data.get('owner_name'),
                "roll_number": vehicle_data.get('roll_number')
            })
            print(f"✅ Vehicle is known. Owner: {plate_info['owner']}, Roll Number: {plate_info['roll_number']}")
        else:
            print("❌ Unknown vehicle detected.")

        # Append plate information to response data
        response_data["plates"].append(plate_info)

        
    
    return jsonify(response_data)

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)