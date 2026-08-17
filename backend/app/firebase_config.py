"""
Firebase Configuration for AI Campus Companion
"""
import firebase_admin
from firebase_admin import credentials, auth
from pathlib import Path
import json
from app.config import get_settings

def initialize_firebase():
    """Initialize Firebase Admin SDK from credentials file"""
    try:
        # Get settings from environment
        settings = get_settings()

        # Check if already initialized
        if not firebase_admin._apps:
            # Try to load from file first
            # Look in multiple possible locations
            possible_paths = [
                Path(__file__).parent.parent.parent / "FIREBASE_CREDENTIALS.json",  # Local project root
                Path(__file__).parent.parent.parent / "backend" / "FIREBASE_CREDENTIALS.json",  # If in root
                Path.cwd() / "FIREBASE_CREDENTIALS.json",  # Current working directory
                Path.cwd() / "backend" / "FIREBASE_CREDENTIALS.json",  # In backend directory
            ]

            credentials_file = None
            for path in possible_paths:
                if path.exists():
                    credentials_file = path
                    break

            if credentials_file:
                with open(credentials_file, 'r') as f:
                    firebase_credentials = json.load(f)
                print(f"Firebase credentials loaded from: {credentials_file}")
                cred = credentials.Certificate(firebase_credentials)
                firebase_admin.initialize_app(cred)
            else:
                print("FIREBASE_CREDENTIALS.json not found in any location")
                print(f"Searched paths: {[str(p) for p in possible_paths]}")
                # Fallback to environment variables
                if settings.firebase_project_id:
                    cred = credentials.Certificate({
                        "type": "service_account",
                        "project_id": settings.firebase_project_id,
                        "private_key_id": settings.firebase_private_key_id,
                        "private_key": settings.firebase_private_key,
                        "client_email": settings.firebase_client_email,
                        "client_id": settings.firebase_client_id,
                        "auth_uri": settings.firebase_auth_uri,
                        "token_uri": settings.firebase_token_uri,
                        "auth_provider_x509_cert_url": settings.firebase_auth_provider_x509_cert_url,
                        "client_x509_cert_url": settings.firebase_client_x509_cert_url,
                    })
                    firebase_admin.initialize_app(cred)
                else:
                    raise Exception("No Firebase credentials found")

        return firebase_admin.get_app()
    except Exception as e:
        print(f"Firebase initialization error: {e}")
        import traceback
        traceback.print_exc()
        return None
