from core.firebase import db_async, verify_token
from fastapi import APIRouter, Depends, HTTPException, Request
from firebase_admin import auth
from google.cloud import firestore as gcloud_firestore

router = APIRouter()


@router.post("/google")
async def google_auth(body: dict):
    token = body.get("token")
    if not token:
        raise HTTPException(status_code=401, detail="no token provided")
    try:
        decoded = auth.verify_id_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    uid = decoded["uid"]
    email = decoded.get("email")
    name = decoded.get("name")
    picture = decoded.get("picture")

    user_ref = db_async.collection("users").document(uid)
    user_doc = await user_ref.get()

    if not user_doc.exists:
        await user_ref.set(
            {
                "uid": uid,
                "email": email,
                "name": name,
                "picture": picture,
                "created_at": gcloud_firestore.SERVER_TIMESTAMP,
                "last_login": gcloud_firestore.SERVER_TIMESTAMP,
            }
        )
        is_new_user = True
    else:
        await user_ref.update(
            {
                "last_login": gcloud_firestore.SERVER_TIMESTAMP,
            }
        )
        is_new_user = False

    return {
        "uid": uid,
        "email": email,
        "name": name,
        "picture": picture,
        "is_new_user": is_new_user,
    }


@router.get("/me")
async def get_me(req: Request, _=Depends(verify_token)):
    uid = req.state.user["uid"]
    user_ref = db_async.collection("users").document(uid)
    user_doc = await user_ref.get()

    if not user_doc.exists:
        raise HTTPException(status_code=404, detail="User not found")

    return user_doc.to_dict()
