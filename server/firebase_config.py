# firebase_config.py
import firebase_admin
from firebase_admin import credentials, firestore
import os
import base64
import json

# Get base64 string from Render environment variable
encoded_key = os.environ.get("SERVICE_ACCOUNT_KEY_BASE64")
if not encoded_key:
    raise ValueError("Missing SERVICE_ACCOUNT_KEY_BASE64 environment variable.")

# Decode and convert to dictionary
decoded_key = base64.b64decode(encoded_key)
key_dict = json.loads(decoded_key)

# Initialize Firebase with the decoded credentials
cred = credentials.Certificate(key_dict)
firebase_admin.initialize_app(cred)

# Initialize Firestore
db = firestore.client()