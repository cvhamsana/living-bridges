# Architecture and workflow

This follows the uploaded proposal's narrow prototype boundary: identify a dog from a nose photo/short video and assign a persistent Dog ID, with a QR tag as a fallback. It does not implement the wider Living Bridges platform.

```text
Caregiver / field volunteer
  ├─ local web prototype upload
  └─ WhatsApp Cloud API (integration placeholder; credentials required)
             ↓
         FastAPI server
             ↓
  video frame parsing (OpenCV)
             ↓
  Laplacian sharpness ranking → best frame
             ↓
  CLAHE contrast enhancement → placeholder central crop
             ↓
  feature-vector extraction (local visual descriptor by default;
  optional ImageNet ResNet50 feature extractor)
             ↓
  cosine similarity against stored vectors
             ↓
  candidate match / low confidence / no match
             ↓
  registration form → unique Dog ID → JSON registry + QR PNG
```

## Important engineering boundaries
- The current central crop is a placeholder, not a snout detector. A real detector needs training/validation.
- ResNet50 ImageNet features are not automatically a canine nose-print biometric model.
- The default local descriptor exists to test the API and UI only; it is not suitable for real identity decisions.
- JSON storage is appropriate only for a local demonstration. Production needs database migrations, authentication, role-based access, backups, audit logs, encryption and privacy review.
- Similarity thresholds in `.env` are configurable examples based on the proposal's bands; they are not validated probabilities.
- QR payloads contain a Dog ID and random token, not a caregiver phone number. A production QR resolution route and token verification still need implementing.
- The WhatsApp webhook endpoint is a placeholder; no live message/media handling or outbound messages are enabled.
