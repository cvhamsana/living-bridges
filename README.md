# Living Bridges — Canine Nose-Print Recognition Prototype

A starter prototype aligned to the uploaded **Canine Nose-Print Recognition Prototype Proposal**.

## Scope reflected in this starter
- WhatsApp-style entry flow: identify unknown dog, register known new dog, update an existing record.
- Video upload endpoint for a short nose video; selects the sharpest frame using OpenCV Laplacian variance.
- Image enhancement using CLAHE.
- ResNet50 feature-vector extraction (optional dependency; a safe fallback is provided for local development).
- Cosine-similarity search over registered dog profiles.
- Confidence bands are **illustrative proposal thresholds only**, not validated accuracy: match >= 85%, review 65–84%, no match < 65%.
- New-dog registration and unique persistent Dog ID.
- Printable QR fallback tag per dog.
- Basic privacy-minded caregiver token masking.
- Cute pastel frontend with a live API status check, registration form, image/video lookup and dog profile cards.

## What this is not
This is a **development starter**, not a validated biometric product. Nose-print matching must be tested on real field data before claiming accuracy. The local feature fallback is only for testing the API flow and must not be used as biometric evidence. WhatsApp Cloud API credentials, webhook verification, and production deployment are not configured automatically. The included frontend demo works without credentials.

## Quick start (Windows PowerShell)
1. Install Python 3.10 or 3.11.
2. Open a terminal in `backend`.
3. Create and activate a virtual environment:
   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   copy .env.example .env
   uvicorn app.main:app --reload
   ```
4. Open `frontend/index.html` in your browser, or serve it:
   ```powershell
   cd ../frontend
   py -m http.server 5500
   ```
   Visit `http://127.0.0.1:5500`.
5. API docs: `http://127.0.0.1:8000/docs`.

## Quick start (macOS/Linux)
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

## Optional AI model
Set `USE_RESNET50=true` in `.env` to use torchvision ResNet50 ImageNet features. Depending on your environment, PyTorch/torchvision installation may need a matching version. For a reproducible real project, train/evaluate on a labelled dog-nose dataset and save an evaluated embedding model. The starter's default is `false` to keep setup light and avoid implying the fallback is real recognition.

## WhatsApp Cloud API integration
Set `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, and `WHATSAPP_VERIFY_TOKEN` in `.env` only after configuring a Meta app. This starter includes a webhook verification route and a basic inbound webhook placeholder; sending media and replies through Meta must be completed with valid credentials and tested against the current Meta API requirements.

## Important safety and evaluation notes
- Similarity scores are not probabilities or validated accuracy.
- Nose texture can change with injury, age, dirt, wetness and lighting.
- The prototype should refuse low-quality images and allow QR/manual fallback.
- Protect phone numbers and location data; do not publish caregiver contact details.
- Medical/vaccination/sterilisation data must be guardian/NGO verified and timestamped.
- This prototype is for identification and unique ID only; it does not implement feeding coordination, ABC workflows, dashboards or funding.

## Project layout
- `backend/app/main.py` — FastAPI endpoints
- `backend/app/recognition.py` — video/image pipeline and embedding extraction
- `backend/app/store.py` — JSON-backed local dog registry for proof of concept
- `backend/app/qr_tags.py` — QR generation
- `backend/app/schemas.py` — data models
- `backend/frontend/` is not used; the frontend lives in root `frontend/`
- `docs/` — architecture and testing notes

## Test
```bash
cd backend
pytest
```
