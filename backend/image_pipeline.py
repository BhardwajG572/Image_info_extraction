"""
Image preprocessing: forced horizontal flip + CLAHE contrast enhancement.

Every uploaded image is horizontally mirrored and then pushed through a 
Contrast Limited Adaptive Histogram Equalization (CLAHE) filter. 
This is a fixed, deterministic transform applied to every image to pull 
out the hidden edges of black-on-black embossed tire text before it goes 
to the VLM for extraction.
"""
import base64
import io
import cv2
import numpy as np

from PIL import Image


def hflip(image_bytes: bytes) -> bytes:
    """Mirror the image horizontally, apply CLAHE contrast, and return PNG bytes."""
    # 1. Load image with PIL and convert to RGB
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    
    # 2. Apply the deterministic horizontal flip
    flipped = img.transpose(Image.FLIP_LEFT_RIGHT)
    
    # 3. Convert PIL image to OpenCV format (NumPy array)
    img_np = np.array(flipped)
    
    # 4. Convert to LAB color space to isolate the Lightness (L) channel
    lab = cv2.cvtColor(img_np, cv2.COLOR_RGB2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)
    
    # 5. Apply CLAHE to the Lightness channel to make the embossing pop
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    cl = clahe.apply(l_channel)
    
    # 6. Merge the enhanced lightness back with the color channels
    limg = cv2.merge((cl, a_channel, b_channel))
    enhanced_np = cv2.cvtColor(limg, cv2.COLOR_LAB2RGB)
    
    # 7. Convert back to PIL Image and save to bytes
    enhanced_img = Image.fromarray(enhanced_np)
    buf = io.BytesIO()
    enhanced_img.save(buf, format="PNG")
    
    return buf.getvalue()


def hflip_b64(image_b64: str) -> str:
    """Same as hflip, but base64 in -> base64 out. This is the function
    frontend/app.py calls on every uploaded image before sending it to
    /extract, and also to render the corrected preview."""
    raw = base64.b64decode(image_b64)
    processed = hflip(raw)
    return base64.b64encode(processed).decode("utf-8")