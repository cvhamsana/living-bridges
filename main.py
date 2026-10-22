import os, tempfile
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from dotenv import load_dotenv

from .schemas import DogRegistration, MatchResult
from .store import DogStore
from .recognition import process_image_bytes, process_video_file, cosine_similarity
from .qr_tags import make_qr_tag

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")
DATA_FILE = os.getenv("DATA_FILE", str(ROOT / "data" / "dogs.json"))
QR_DIR = os.getenv("QR_DIR", str(ROOT / "data" / "qr"))
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", str(ROOT / "data" / "uploads")))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
USE_RESNET50 = os.getenv("USE_RESNET50", "false").lower() == "true"
MATCH_THRESHOLD = float(os.getenv("MATCH_THRESHOLD", "0.85"))
REVIEW_THRESHOLD = float(os.getenv("REVIEW_THRESHOLD", "0.65"))
store = DogStore(DATA_FILE)

app = FastAPI(title="Living Bridges — Canine Nose-Print Prototype", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False, allow_methods=["*"], allow_headers=["*"])

def profile_out(row: dict) -> dict:
    return store.public(row)

def match_embedding(embedding: list[float] | None):
    if not embedding:
        return {"status":"quality_retry","message":"We couldn't create a usable image signature. Please send a clearer, well-lit nose photo or a short 2-second video."}
    candidates = []
    for row in store.all():
        score = cosine_similarity(embedding, row.get("embedding"))
        if score >= 0:
            candidates.append((score, row))
    if not candidates:
        return {"status":"no_match","message":"No comparable registered nose signature was available. You can register this dog or use its QR tag.","similarity":None}
    score, row = max(candidates, key=lambda x:x[0])
    # Scores and thresholds are prototype demonstration bands, not validated biometric accuracy.
    if score >= MATCH_THRESHOLD:
        return {"status":"match_found","message":"Possible registered match found. Verify the record before acting on it.","dog":profile_out(row),"similarity":round(score,4)}
    if score >= REVIEW_THRESHOLD:
        return {"status":"low_confidence","message":"Possible low-confidence match. Try a clearer video or use the QR fallback; manual review is recommended.","dog":profile_out(row),"similarity":round(score,4)}
    return {"status":"no_match","message":"No confident match found. You can register this dog after checking for duplicates.","similarity":round(score,4)}

@app.get("/")
def root():
    return {"service":"Living Bridges Canine Nose-Print Prototype","status":"running","docs":"/docs","note":"Proof of concept only; no validated accuracy claims."}

@app.get("/api/health")
def health():
    return {"status":"ok","service":"Living Bridges API","resnet50_enabled":USE_RESNET50,"registered_dogs":len(store.all())}

@app.get("/api/dogs")
def list_dogs():
    return {"dogs":[profile_out(r) for r in store.all()], "count":len(store.all())}

@app.get("/api/dogs/{dog_id}")
def get_dog(dog_id: str):
    row = store.get(dog_id)
    if not row:
        raise HTTPException(404, "Dog ID not found")
    return profile_out(row)

@app.post("/api/register")
async def register_dog(
    name: str = Form("Unnamed"), area: str = Form(...),
    age_group: str = Form("Unknown"), sex: str = Form("Unknown"),
    vaccination_status: str = Form("Unknown"), vaccination_date: str = Form(""),
    sterilization_status: str = Form("Unknown"), distinguishing_marks: str = Form(""),
    caregiver_name: str = Form(""), caregiver_contact: str = Form(""),
    care_notes: str = Form(""), image: UploadFile = File(...)
):
    payload = DogRegistration(
        name=name or "Unnamed", area=area, age_group=age_group, sex=sex,
        vaccination_status=vaccination_status, vaccination_date=vaccination_date or None,
        sterilization_status=sterilization_status, distinguishing_marks=distinguishing_marks or None,
        caregiver_name=caregiver_name or None, caregiver_contact=caregiver_contact or None,
        care_notes=care_notes or None
    ).model_dump()
    data = await image.read()
    if len(data) > 20 * 1024 * 1024:
        raise HTTPException(413, "File is too large; maximum upload is 20 MB.")
    embedding = None
    if image.content_type and image.content_type.startswith("video/"):
        suffix = Path(image.filename or "clip.mp4").suffix or ".mp4"
        tmp_path = UPLOAD_DIR / f"registration{suffix}"
        tmp_path.write_bytes(data)
        crop, embedding, sharpness, error = process_video_file(str(tmp_path), USE_RESNET50)
        tmp_path.unlink(missing_ok=True)
        if error:
            raise HTTPException(400, error)
    else:
        crop, embedding, sharpness = process_image_bytes(data, USE_RESNET50)
    if crop is None:
        raise HTTPException(400, "Image could not be read. Please upload JPG, PNG, or a supported video.")
    # Duplicate warning is intentionally non-blocking and requires manual review in this starter.
    possible_duplicates = []
    for existing in store.all():
        score = cosine_similarity(embedding, existing.get("embedding"))
        if score >= 0.55:
            possible_duplicates.append({"dog_id":existing["dog_id"],"similarity":round(score,4)})
    token = os.urandom(16).hex()
    # create first to get permanent ID; then QR generation
    row = store.add(payload, embedding, None)
    qr_path = make_qr_tag(row["dog_id"], token, QR_DIR)
    row = store.update(row["dog_id"], {"qr_file": qr_path})
    return {
        "message":"Dog registered. Please manually review any possible duplicate suggestions before treating the record as unique.",
        "dog":profile_out(row), "qr_download":f"/api/dogs/{row['dog_id']}/qr",
        "possible_duplicates":possible_duplicates, "sharpness_score":round(sharpness,2),
        "embedding_note":"A local visual descriptor is used unless USE_RESNET50=true; neither option is a validated canine nose-print model."
    }

@app.post("/api/identify/image", response_model=MatchResult)
async def identify_image(image: UploadFile = File(...)):
    data = await image.read()
    if len(data) > 20 * 1024 * 1024:
        raise HTTPException(413, "File is too large; maximum upload is 20 MB.")
    if image.content_type and image.content_type.startswith("video/"):
        suffix = Path(image.filename or "clip.mp4").suffix or ".mp4"
        tmp_path = UPLOAD_DIR / f"lookup{suffix}"
        tmp_path.write_bytes(data)
        crop, embedding, sharpness, error = process_video_file(str(tmp_path), USE_RESNET50)
        tmp_path.unlink(missing_ok=True)
        if error:
            return MatchResult(status="quality_retry", message=error)
    else:
        crop, embedding, sharpness = process_image_bytes(data, USE_RESNET50)
    if crop is None:
        return MatchResult(status="quality_retry", message="Could not read this file. Please upload a clear JPG/PNG or supported short video.")
    if sharpness < 8:
        return MatchResult(status="quality_retry", message="The image looks very blurry. Try a brighter, steadier nose photo or use a QR tag.")
    result = match_embedding(embedding)
    result["message"] += f" (Image sharpness score: {sharpness:.1f}; this is a technical quality measure, not recognition accuracy.)"
    return MatchResult(**result)

@app.get("/api/dogs/{dog_id}/qr")
def get_qr(dog_id: str):
    row = store.get(dog_id)
    if not row or not row.get("qr_file") or not Path(row["qr_file"]).exists():
        raise HTTPException(404, "QR tag not found")
    return FileResponse(row["qr_file"], media_type="image/png", filename=f"{dog_id}-qr.png")

@app.patch("/api/dogs/{dog_id}")
async def update_dog(dog_id: str, request: Request):
    row = store.get(dog_id)
    if not row:
        raise HTTPException(404, "Dog ID not found")
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(400, "Send a JSON object with fields to update.")
    allowed = {"name","area","age_group","sex","vaccination_status","vaccination_date","sterilization_status","distinguishing_marks","caregiver_name","caregiver_contact","care_notes"}
    changes = {k:v for k,v in data.items() if k in allowed}
    updated = store.update(dog_id, changes)
    return {"message":"Record updated","dog":profile_out(updated)}

@app.get("/webhook/whatsapp")
def verify_whatsapp(
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token")
):
    expected = os.getenv("WHATSAPP_VERIFY_TOKEN", "")
    if hub_mode == "subscribe" and hub_challenge and expected and hub_verify_token == expected:
        return PlainTextResponse(hub_challenge)
    raise HTTPException(403, "WhatsApp webhook verification failed. Configure the verify token first.")

@app.post("/webhook/whatsapp")
async def whatsapp_inbound_placeholder(request: Request):
    # Deliberately no outgoing reply until Meta credentials and media download are configured.
    payload = await request.json()
    return {"received":True,"integration":"placeholder","message":"Webhook payload accepted by prototype endpoint; configure Meta credentials and implement signed event/media handling before live use.","top_level_keys":list(payload.keys())[:10]}
