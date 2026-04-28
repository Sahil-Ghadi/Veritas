import os

import firebase_admin
from dotenv import load_dotenv
from fastapi import HTTPException, Request
from firebase_admin import auth, credentials, firestore, firestore_async

load_dotenv()


def init_firebase():
    """
    Initialise the Firebase Admin SDK once.

    Supports both:
    1. File path via FIREBASE_SERVICE_ACCOUNT_PATH
    2. Base64 encoded content via FIREBASE_SERVICE_ACCOUNT_BASE64 (for deployment)
    """
    # Check for base64 encoded content first (for Render/deployment)
    base64_content = os.getenv("FIREBASE_SERVICE_ACCOUNT_BASE64")
    if base64_content:
        try:
            import base64
            import json
            decoded = base64.b64decode(base64_content).decode('utf-8')
            cred_dict = json.loads(decoded)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            return
        except Exception as e:
            raise RuntimeError(f"Failed to decode FIREBASE_SERVICE_ACCOUNT_BASE64: {e}")
    
    # Fall back to file path (for local dev)
    key_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH", "serviceAccountKey.json")
    try:
        cred = credentials.Certificate(key_path)
        firebase_admin.initialize_app(cred)
    except ValueError:
        # App already initialised (e.g. module re-imported in tests / hot-reload)
        pass
    except FileNotFoundError:
        raise RuntimeError(
            f"Firebase service account key not found at '{key_path}'. "
            "Set FIREBASE_SERVICE_ACCOUNT_PATH in your .env file or place "
            "serviceAccountKey.json in the project root."
        )


# ── Initialise SDK on module import ───────────────────────────────────────────
init_firebase()

# Synchronous Firestore client — used by existing auth routes
db = firestore.client()

# Asynchronous Firestore client — used by the dispute system and any new
# async services.  Both clients share the same underlying Firebase app/project.
db_async = firestore_async.client()


# ── Auth dependency ───────────────────────────────────────────────────────────
async def verify_token(req: Request):
    auth_header = req.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid Authorization header",
        )

    token = auth_header.replace("Bearer ", "")
    try:
        decoded = auth.verify_id_token(token)
        req.state.user = decoded
        return decoded
    except auth.ExpiredIdTokenError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except auth.InvalidIdTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")
