from pathlib import Path
import qrcode

def make_qr_tag(dog_id: str, verification_token: str, out_dir: str) -> str:
    directory = Path(out_dir)
    directory.mkdir(parents=True, exist_ok=True)
    # Only the ID and a random verification token are encoded; no phone number.
    payload = f"living-bridges://dog/{dog_id}?token={verification_token}"
    img = qrcode.make(payload)
    path = directory / f"{dog_id}.png"
    img.save(path)
    return str(path)
