from fastapi import APIRouter, HTTPException, Request, Depends
from firebase_admin import auth, firestore
from core.firebase import db, verify_token

router = APIRouter()
@router.post("/google")
async def google_auth(body: dict):
    token = body.get("token")
    if not token:
        raise HTTPException(status_code=401, detail="no token provided")
    try:
        decoded = auth.verify_id_token(token)
    except:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    uid = decoded['uid']
    email = decoded.get("email")
    name = decoded.get("name")
    picture = decoded.get("picture")

    user_ref = db.collection("users").document(uid)
    user_doc = user_ref.get()
    if not user_doc.exists:
        user_ref.set({
            "uid": uid,
            "email": email,
            "name": name,
            "picture": picture,
            "created_at": firestore.SERVER_TIMESTAMP
        })
        is_new_user = True
    else:
        is_new_user = False
    return {
        "uid": uid,
        "email": email,
        "name": name,
        "picture": picture,
        "is_new_user": is_new_user
    }

@router.get("/me")
async def get_me(req: Request, _ = Depends(verify_token)):
    uid = req.state.user['uid']
    user_ref = db.collection('users').document(uid)
    user_doc = user_ref.get()

    if not user_doc.exists:
        raise HTTPException(status_code=404, detail="User not found")

    return user_doc.to_dict()