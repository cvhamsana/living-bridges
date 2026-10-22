import os, tempfile
from pathlib import Path
import cv2
import numpy as np

def select_sharpest_frame(video_path: str) -> tuple[np.ndarray | None, float]:
    cap = cv2.VideoCapture(video_path)
    best_frame, best_score = None, -1.0
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
            if score > best_score:
                best_score, best_frame = score, frame
    finally:
        cap.release()
    if best_frame is None:
        return None, 0.0
    return best_frame, best_score

def enhance_image(frame: np.ndarray) -> np.ndarray:
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = cv2.merge((clahe.apply(l), a, b))
    return cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)

def crop_central_snout(frame: np.ndarray) -> np.ndarray:
    # Placeholder crop only. Real deployment should use a validated snout detector.
    h, w = frame.shape[:2]
    x1, x2 = int(w * .18), int(w * .82)
    y1, y2 = int(h * .18), int(h * .82)
    crop = frame[y1:y2, x1:x2]
    return crop if crop.size else frame

def embedding_from_image(image: np.ndarray, use_resnet50: bool = False) -> list[float] | None:
    if use_resnet50:
        try:
            import torch
            from torchvision.models import resnet50, ResNet50_Weights
            from PIL import Image
            weights = ResNet50_Weights.DEFAULT
            model = resnet50(weights=weights)
            model.fc = torch.nn.Identity()
            model.eval()
            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            pil = Image.fromarray(rgb).resize((224,224))
            tensor = weights.transforms()(pil).unsqueeze(0)
            with torch.no_grad():
                vec = model(tensor).squeeze().cpu().numpy().astype(np.float32)
            norm = np.linalg.norm(vec)
            return (vec / norm).tolist() if norm else None
        except Exception:
            return None
    # Deterministic visual descriptor for API/UI plumbing only. Not a biometric model.
    resized = cv2.resize(image, (32,32), interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
    hist = cv2.calcHist([resized], [0,1,2], None, [8,8,8], [0,256,0,256,0,256]).flatten()
    hist = hist / (np.linalg.norm(hist) + 1e-12)
    # Include low-resolution grayscale pattern to give a deterministic vector.
    pattern = gray.flatten()
    pattern = pattern / (np.linalg.norm(pattern) + 1e-12)
    vec = np.concatenate([hist, pattern]).astype(np.float32)
    vec = vec / (np.linalg.norm(vec) + 1e-12)
    return vec.tolist()

def process_image_bytes(data: bytes, use_resnet50: bool = False) -> tuple[np.ndarray | None, list[float] | None, float]:
    arr = np.frombuffer(data, dtype=np.uint8)
    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if frame is None:
        return None, None, 0.0
    enhanced = enhance_image(frame)
    crop = crop_central_snout(enhanced)
    embedding = embedding_from_image(crop, use_resnet50=use_resnet50)
    sharpness = float(cv2.Laplacian(cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var())
    return crop, embedding, sharpness

def process_video_file(path: str, use_resnet50: bool = False):
    frame, sharpness = select_sharpest_frame(path)
    if frame is None:
        return None, None, 0.0, "Could not read video frames. Try MP4/MOV with a clear 2-second nose view."
    enhanced = enhance_image(frame)
    crop = crop_central_snout(enhanced)
    emb = embedding_from_image(crop, use_resnet50=use_resnet50)
    return crop, emb, sharpness, None

def cosine_similarity(a: list[float] | None, b: list[float] | None) -> float:
    if not a or not b or len(a) != len(b):
        return -1.0
    av, bv = np.asarray(a, dtype=np.float32), np.asarray(b, dtype=np.float32)
    denom = float(np.linalg.norm(av) * np.linalg.norm(bv))
    if denom == 0:
        return -1.0
    return float(np.dot(av, bv) / denom)
