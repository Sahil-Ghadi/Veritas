import firebase_admin
from firebase_admin import credentials, auth, firestore
from fastapi import Request, HTTPException

def init_firebase():
    try:
        cred = credentials.Certificate("serviceAccountKey.json")
        firebase_admin.initialize_app(cred)
    except ValueError:
        # Firebase app already initialized
        pass
    except FileNotFoundError:
        raise RuntimeError("serviceAccountKey.json file not found. Ensure it is in the correct location.")

# Initialize Firebase on module import
init_firebase()
db = firestore.client()

async def verify_token(req: Request):
    auth_header = req.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    
    token = auth_header.replace("Bearer ", "")
    try:
        decoded = auth.verify_id_token(token)
        req.state.user = decoded
        return decoded
    except auth.InvalidIdTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except auth.ExpiredIdTokenError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")