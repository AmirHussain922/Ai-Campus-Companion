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
            credentials_file = Path(__file__).parent.parent.parent / "FIREBASE_CREDENTIALS.json"

            if credentials_file.exists():
                with open(credentials_file, 'r') as f:
                    firebase_credentials = json.load(f)

                cred = credentials.Certificate(firebase_credentials)
                firebase_admin.initialize_app(cred)
            else:
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
        return None
