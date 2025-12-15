"""
Firebase Admin SDK initialization.
"""
import os
import json
import firebase_admin
from firebase_admin import credentials, firestore

# Global Firestore client
_db = None


def get_db():
    """Get or initialize Firestore database client."""
    global _db
    
    if _db is not None:
        return _db
    
    # Check if already initialized
    if firebase_admin._apps:
        _db = firestore.client()
        return _db
    
    # Try to get credentials from environment
    creds_json = os.getenv("FIREBASE_CREDENTIALS_JSON")
    creds_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
    
    if creds_json:
        # Parse JSON from environment variable
        try:
            creds_dict = json.loads(creds_json)
            cred = credentials.Certificate(creds_dict)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid FIREBASE_CREDENTIALS_JSON: {e}")
    elif creds_path:
        # Load from file path
        if not os.path.exists(creds_path):
            raise FileNotFoundError(f"Firebase credentials file not found: {creds_path}")
        cred = credentials.Certificate(creds_path)
    else:
        # Try default location
        default_path = os.path.join(os.path.dirname(__file__), "firebase-credentials.json")
        if os.path.exists(default_path):
            cred = credentials.Certificate(default_path)
        else:
            raise ValueError(
                "Firebase credentials not found. Set FIREBASE_CREDENTIALS_JSON, "
                "FIREBASE_CREDENTIALS_PATH, or place firebase-credentials.json in backend/"
            )
    
    # Initialize Firebase app
    firebase_admin.initialize_app(cred)
    _db = firestore.client()
    
    print("[FIREBASE] Initialized successfully")
    return _db


def test_connection():
    """Test Firebase connection."""
    try:
        db = get_db()
        # Try to access a collection
        db.collection("_test").limit(1).get()
        return True
    except Exception as e:
        print(f"[FIREBASE] Connection test failed: {e}")
        return False
