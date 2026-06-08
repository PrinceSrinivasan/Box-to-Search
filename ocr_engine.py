import asyncio
import io
import requests
from PIL import Image, ImageOps
from winrt.windows.graphics.imaging import BitmapPixelFormat, SoftwareBitmap
from winrt.windows.media.ocr import OcrEngine
import winrt.windows.storage.streams as streams
import config_manager

def load_image_as_software_bitmap(image):
    """
    Converts a PIL Image object to a WinRT SoftwareBitmap.
    """
    width, height = image.size
    data_writer = streams.DataWriter()
    data_writer.write_bytes(image.convert("RGBA").tobytes())
    bitmap = SoftwareBitmap(BitmapPixelFormat.RGBA8, width, height)
    bitmap.copy_from_buffer(data_writer.detach_buffer())
    return bitmap

async def run_ocr_words(image, scale, pad):
    """
    Runs Windows native OCR on the given preprocessed PIL Image and returns
    a list of words with their coordinates normalized back to the original image space.
    """
    engine = OcrEngine.try_create_from_user_profile_languages()
    if not engine:
        return []
        
    try:
        bitmap = load_image_as_software_bitmap(image)
        result = await engine.recognize_async(bitmap)
        
        words = []
        for line in result.lines:
            for word in line.words:
                rect = word.bounding_rect
                orig_x = (rect.x - pad) / scale
                orig_y = (rect.y - pad) / scale
                orig_w = rect.width / scale
                orig_h = rect.height / scale
                words.append({
                    "text": word.text,
                    "x": orig_x,
                    "y": orig_y,
                    "w": orig_w,
                    "h": orig_h
                })
        return words
    except Exception:
        return []

def calculate_overlap_ratio(w1, w2):
    """
    Calculates the intersection-over-minimum (IoMin) overlap ratio of two word bounding boxes.
    """
    x1_start, y1_start = w1["x"], w1["y"]
    x1_end, y1_end = w1["x"] + w1["w"], w1["y"] + w1["h"]
    
    x2_start, y2_start = w2["x"], w2["y"]
    x2_end, y2_end = w2["x"] + w2["w"], w2["y"] + w2["h"]
    
    x_start = max(x1_start, x2_start)
    y_start = max(y1_start, y2_start)
    x_end = min(x1_end, x2_end)
    y_end = min(y1_end, y2_end)
    
    if x_start < x_end and y_start < y_end:
        intersection_area = (x_end - x_start) * (y_end - y_start)
        area1 = w1["w"] * w1["h"]
        area2 = w2["w"] * w2["h"]
        min_area = min(area1, area2)
        if min_area <= 0:
            return 0
        return intersection_area / min_area
    return 0

def clean_and_reconstruct(all_words):
    """
    Deduplicates overlapping words across passes and reconstructs the spatial layout.
    """
    if not all_words:
        return ""

    # Sort words by clean alphanumeric length descending, penalizing extra non-alphanumeric noise
    def get_score(w):
        clean_txt = "".join(c for c in w["text"] if c.isalnum())
        # Penalize non-alphanumeric trailing/leading characters slightly to break ties
        penalty = 0.1 * (len(w["text"]) - len(clean_txt))
        return len(clean_txt) - penalty
        
    sorted_words = sorted(all_words, key=get_score, reverse=True)
    
    accepted_words = []
    for w in sorted_words:
        # Avoid empty words
        if not w["text"].strip():
            continue
        # Check if it overlaps significantly with any already accepted word
        overlaps = False
        for acc in accepted_words:
            if calculate_overlap_ratio(w, acc) > 0.4:
                overlaps = True
                break
        if not overlaps:
            accepted_words.append(w)
            
    # Reconstruct lines: group words by Y vertical overlap
    # Sort accepted words by Y coordinate first
    accepted_words = sorted(accepted_words, key=lambda w: w["y"])
    
    lines = []
    for w in accepted_words:
        placed = False
        for line in lines:
            # Check overlap with line bounding box (min Y to max Y+H)
            line_y_start = min(lw["y"] for lw in line)
            line_y_end = max(lw["y"] + lw["h"] for lw in line)
            line_h = line_y_end - line_y_start
            
            y_start = max(w["y"], line_y_start)
            y_end = min(w["y"] + w["h"], line_y_end)
            
            if y_start < y_end:
                overlap_h = y_end - y_start
                min_h = min(w["h"], line_h)
                if min_h > 0 and (overlap_h / min_h) > 0.4:
                    line.append(w)
                    placed = True
                    break
        if not placed:
            lines.append([w])
            
    # Sort lines by average Y coordinate (top to bottom)
    def get_line_avg_y(line):
        return sum(lw["y"] + lw["h"]/2 for lw in line) / len(line)
        
    lines = sorted(lines, key=get_line_avg_y)
    
    # Sort words within each line by X coordinate (left to right) and join
    reconstructed_lines = []
    for line in lines:
        sorted_line = sorted(line, key=lambda lw: lw["x"])
        line_text = " ".join(lw["text"] for lw in sorted_line)
        reconstructed_lines.append(line_text)
        
    return "\n".join(reconstructed_lines).strip()

async def extract_text_online_async(image):
    """
    Asynchronously extracts text from an image using the online OCR.space API.
    """
    buf = io.BytesIO()
    image.convert("RGB").save(buf, format="JPEG")
    buf.seek(0)
    
    config = config_manager.load_config()
    lang_code = config.get("default_language", "en")
    
    ocr_space_lang = "eng"
    lang_map = {
        "en": "eng", "es": "spa", "fr": "fre", "de": "ger", "it": "ita",
        "pt": "por", "ru": "rus", "ja": "jpn", "zh-CN": "chs", "zh-TW": "cht",
        "hi": "hin", "ar": "ara", "ko": "kor", "tr": "tur", "vi": "vie",
        "nl": "dut", "pl": "pol"
    }
    ocr_space_lang = lang_map.get(lang_code, "eng")
    
    def post_request():
        url = "https://api.ocr.space/parse/image"
        payload = {
            "apikey": "helloworld",
            "language": ocr_space_lang,
            "OCREngine": "3",
            "isOverlayRequired": False
        }
        files = {
            "file": ("image.jpg", buf, "image/jpeg")
        }
        try:
            response = requests.post(url, data=payload, files=files, timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get("IsErroredOnProcessing"):
                    return f"Online OCR Error: {result.get('ErrorMessage')}"
                
                parsed_results = result.get("ParsedResults", [])
                if parsed_results:
                    raw_text = parsed_results[0].get("ParsedText", "").strip()
                    import re
                    match = re.match(r"^```[a-zA-Z0-9_\-\+]*\s*\n(.*?)\n```$", raw_text, re.DOTALL)
                    if match:
                        return match.group(1).strip()
                    if raw_text.startswith("```") and raw_text.endswith("```"):
                        lines = raw_text.splitlines()
                        if len(lines) >= 2:
                            if lines[0].startswith("```"):
                                lines = lines[1:]
                            if lines and lines[-1].strip() == "```":
                                lines = lines[:-1]
                            return "\n".join(lines).strip()
                        elif len(lines) == 1:
                            inner = raw_text[3:-3].strip()
                            for lang in ["python", "py", "javascript", "js", "cpp", "c", "java", "html", "css"]:
                                if inner.lower().startswith(lang + " "):
                                    inner = inner[len(lang):].strip()
                                    break
                            return inner
                    return raw_text
                return "(No text detected)"
            else:
                return f"Online OCR Error: HTTP {response.status_code}"
        except requests.exceptions.RequestException as e:
            err_msg = str(e)
            if "Failed to resolve" in err_msg or "Max retries exceeded" in err_msg or "Connection" in err_msg:
                return "No internet connection. Please connect to the internet to use online OCR."
            return f"Online OCR Network Error: {err_msg}"
            
    return await asyncio.to_thread(post_request)

async def extract_text_async(image_path_or_pil):
    """
    Asynchronously extracts text from an image using multi-pass offline OCR.
    """
    if isinstance(image_path_or_pil, str):
        try:
            orig_img = Image.open(image_path_or_pil)
        except Exception as e:
            return f"Error opening image: {str(e)}"
    else:
        orig_img = image_path_or_pil

    # Check config for online/offline mode
    config = config_manager.load_config()
    mode = config.get("ocr_mode", "online")
    if mode == "online":
        return await extract_text_online_async(orig_img)

    # Check if Windows OCR engine is available
    engine = OcrEngine.try_create_from_user_profile_languages()
    if not engine:
        return "Error: Windows OCR engine could not be initialized."

    # Dynamic scaling based on image size to preserve OCR quality for small selections
    max_dim = max(orig_img.width, orig_img.height)
    if max_dim < 300:
        scale = 3.0
    elif max_dim < 600:
        scale = 2.0
    else:
        scale = 1.0

    pad_size = 20

    # Define the 3 preprocessing recipes
    # 1. Standard Resize
    def prep_standard(img):
        if scale == 1.0:
            return img
        return img.resize((int(img.width * scale), int(img.height * scale)), Image.Resampling.LANCZOS)

    # 2. Threshold 120 (for isolated/low-contrast pink characters like '6')
    def prep_thresh_120(img):
        # Convert to grayscale first, threshold, then resize (Lanczos creates smooth edges)
        gray = img.convert("L")
        bin_img = gray.point(lambda x: 0 if x < 120 else 255, 'L')
        if scale == 1.0:
            return bin_img
        return bin_img.resize((int(bin_img.width * scale), int(bin_img.height * scale)), Image.Resampling.LANCZOS)

    # 3. Scale first then Threshold 200 (for clean normal text on gradients)
    def prep_thresh_200(img):
        if scale != 1.0:
            img = img.resize((int(img.width * scale), int(img.height * scale)), Image.Resampling.LANCZOS)
        gray = img.convert("L")
        return gray.point(lambda x: 0 if x < 200 else 255, 'L')

    recipes = [
        (scale, pad_size, prep_standard),
        (scale, pad_size, prep_thresh_120),
        (scale, pad_size, prep_thresh_200)
    ]

    all_words = []
    
    # Run all OCR passes concurrently
    tasks = []
    for s, p, prep_func in recipes:
        try:
            proc_img = prep_func(orig_img)
            padded_img = ImageOps.expand(proc_img, border=p, fill=255)
            tasks.append(run_ocr_words(padded_img, s, p))
        except Exception:
            continue

    if tasks:
        results = await asyncio.gather(*tasks)
        for words_list in results:
            all_words.extend(words_list)

    # Reconstruct text layout
    return clean_and_reconstruct(all_words)

def extract_text(image_path_or_pil):
    """
    Synchronous wrapper to extract text.
    """
    try:
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        if loop.is_running():
            new_loop = asyncio.new_event_loop()
            return new_loop.run_until_complete(extract_text_async(image_path_or_pil))
        else:
            return loop.run_until_complete(extract_text_async(image_path_or_pil))
    except Exception as e:
        return f"OCR Error: {str(e)}"
