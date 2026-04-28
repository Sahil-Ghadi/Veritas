import os

import firebase_admin
from dotenv import load_dotenv
from fastapi import HTTPException, Request
from firebase_admin import auth, credentials, firestore, firestore_async

load_dotenv()


def init_firebase():
    """Initialise Firebase Admin SDK using FIREBASE_SERVICE_ACCOUNT_BASE64."""
    base64_content = os.getenv("FIREBASE_SERVICE_ACCOUNT_BASE64")
    if not base64_content:
        env_vars = [k for k in os.environ.keys() if 'FIREBASE' in k or 'GOOGLE' in k]
        raise RuntimeError(
            f"FIREBASE_SERVICE_ACCOUNT_BASE64 not set. "
            f"Env vars found: {env_vars}"
        )
    
    try:
        import base64, json
        decoded = base64.b64decode(base64_content).decode('utf-8')
        cred_dict = json.loads(decoded)
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        raise RuntimeError(f"FIREBASE_SERVICE_ACCOUNT_BASE64 invalid: {e}")


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
