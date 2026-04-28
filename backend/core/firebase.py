import os

import firebase_admin
from dotenv import load_dotenv
from fastapi import HTTPException, Request
from firebase_admin import auth, credentials, firestore, firestore_async

load_dotenv()


def init_firebase():
    """Initialise Firebase Admin SDK. Uses FIREBASE_SERVICE_ACCOUNT_BASE64 or FIREBASE_SERVICE_ACCOUNT_PATH."""
    base64_content = os.getenv("FIREBASE_SERVICE_ACCOUNT_BASE64")
    if base64_content:
        try:
            import base64, json
            decoded = base64.b64decode(base64_content).decode('utf-8')
            cred_dict = json.loads(decoded)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            return
        except Exception as e:
            raise RuntimeError(f"FIREBASE_SERVICE_ACCOUNT_BASE64 set but invalid: {e}")

    key_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH", "serviceAccountKey.json")
    try:
        cred = credentials.Certificate(key_path)
        firebase_admin.initialize_app(cred)
    except ValueError:
        pass
    except FileNotFoundError:
        env_vars = [k for k in os.environ.keys() if 'FIREBASE' in k or 'GOOGLE' in k]
        raise RuntimeError(
            f"Firebase key not found at '{key_path}'. "
            f"Set FIREBASE_SERVICE_ACCOUNT_BASE64 (has value: {bool(base64_content)}) "
            f"or FIREBASE_SERVICE_ACCOUNT_PATH. Env vars found: {env_vars}"
        )


# Initialise SDK on module import
init_firebase()

# Synchronous Firestore client
db = firestore.client()

# Asynchronous Firestore client
db_async = firestore_async.client()


# Auth dependency
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
