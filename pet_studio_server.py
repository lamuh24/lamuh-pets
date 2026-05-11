import base64
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from urllib.parse import urlsplit
import uuid
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

try:
    from PIL import Image, ImageDraw
    from io import BytesIO
except Exception:
    Image = None
    ImageDraw = None
    BytesIO = None


ROOT = Path(__file__).resolve().parent
DEFAULT_PORT = int(os.environ.get("PET_STUDIO_PORT", "8787"))
IMAGE_MODEL = os.environ.get("PET_STUDIO_IMAGE_MODEL", "gpt-image-2")
VISION_MODEL = os.environ.get("PET_STUDIO_VISION_MODEL", "gpt-4.1-mini")
QUALITY = os.environ.get("PET_STUDIO_IMAGE_QUALITY", "medium")
ENABLE_OPENAI = os.environ.get("PET_STUDIO_ENABLE_OPENAI", "").strip() == "1"
MAX_BODY_BYTES = 20 * 1024 * 1024
GENERATED_PETS_DIR = ROOT / "generated_pets"


def slugify(value):
    slug = re.sub(r"[^a-z0-9]+", "-", (value or "custom-pet").lower()).strip("-")
    return (slug or "custom-pet")[:48]


def json_bytes(payload, status=200):
    body = json.dumps(payload, indent=2).encode("utf-8")
    return status, body


def decode_data_url(data_url):
    if not data_url:
        return None, None
    if "," in data_url and data_url.strip().lower().startswith("data:"):
        header, encoded = data_url.split(",", 1)
        mime = header.split(";", 1)[0].replace("data:", "") or "image/png"
        return base64.b64decode(encoded), mime
    return base64.b64decode(data_url), "image/png"


def make_layout_guide(row_id, expected_frames):
    if Image is None:
        return None
    width, height = 1536, 1024
    img = Image.new("RGBA", (width, height), (255, 0, 255, 255))
    draw = ImageDraw.Draw(img)
    cell_w = width // 8
    lane_top = 384
    lane_bottom = 640
    for index in range(8):
        x0 = index * cell_w
        x1 = x0 + cell_w
        outline = (30, 30, 30, 255) if index < expected_frames else (120, 120, 120, 255)
        fill = (255, 0, 255, 255)
        draw.rectangle([x0 + 8, lane_top, x1 - 8, lane_bottom], fill=fill, outline=outline, width=3)
        if index < expected_frames:
            draw.line([x0 + cell_w // 2, lane_top + 12, x0 + cell_w // 2, lane_bottom - 12], fill=(0, 200, 255, 255), width=2)
            draw.line([x0 + 24, lane_top + 36, x1 - 24, lane_top + 36], fill=(255, 220, 80, 255), width=2)
    draw.text((32, 32), f"layout guide only: {row_id}, {expected_frames} active frames", fill=(20, 20, 20, 255))
    buf = BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


def encode_multipart(fields, files):
    boundary = "----pet-studio-%s" % uuid.uuid4().hex
    chunks = []
    for name, value in fields.items():
        chunks.append(f"--{boundary}\r\n".encode("utf-8"))
        chunks.append(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"))
        chunks.append(str(value).encode("utf-8"))
        chunks.append(b"\r\n")
    for field_name, filename, content_type, data in files:
        chunks.append(f"--{boundary}\r\n".encode("utf-8"))
        chunks.append(
            f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'.encode("utf-8")
        )
        chunks.append(f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"))
        chunks.append(data)
        chunks.append(b"\r\n")
    chunks.append(f"--{boundary}--\r\n".encode("utf-8"))
    return boundary, b"".join(chunks)


def openai_json_request(url, payload, api_key, timeout=180):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def openai_multipart_request(url, fields, files, api_key, timeout=180):
    boundary, body = encode_multipart(fields, files)
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def extract_image_b64(result):
    if isinstance(result, dict):
        data = result.get("data") or []
        if data and data[0].get("b64_json"):
            return data[0]["b64_json"]
        output = result.get("output") or []
        for item in output:
            if item.get("type") == "image_generation_call" and item.get("result"):
                return item["result"]
    return None


def extract_response_text(result):
    if not isinstance(result, dict):
        return ""
    if isinstance(result.get("output_text"), str):
        return result["output_text"].strip()
    chunks = []
    for item in result.get("output") or []:
        for content in item.get("content") or []:
            text = content.get("text")
            if isinstance(text, str):
                chunks.append(text)
    return "\n".join(chunks).strip()


class PetStudioHandler(SimpleHTTPRequestHandler):
    server_version = "PetStudio/0.1"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def send_json(self, payload, status=200):
        _, body = json_bytes(payload, status)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        route = urlsplit(self.path).path
        if route == "/api/health":
            self.send_json(
                {
                    "ok": True,
                    "time": int(time.time()),
                    "google_key_present": bool(os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")),
                    "image_generation_enabled": False,
                    "image_model": IMAGE_MODEL,
                    "vision_model": VISION_MODEL,
                    "quality": QUALITY,
                    "note": "Google key powers spawned pet chat and agent features. Built-in image generation is paused for now.",
                }
            )
            return
        if route == "/api/routes":
            self.send_json({"ok": True, "routes": ["GET /api/health", "POST /api/analyze-reference", "POST /api/openai-image", "POST /api/spawn-pet"]})
            return
        super().do_GET()

    def do_POST(self):
        route = urlsplit(self.path).path
        if route == "/api/spawn-pet":
            self.handle_spawn_pet()
            return

        if route == "/api/analyze-reference":
            self.handle_analyze_reference()
            return

        if route != "/api/openai-image":
            self.send_json({"ok": False, "error": "unknown endpoint", "path": self.path, "route": route}, 404)
            return

        self.handle_openai_image()

    def read_json_body(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length > MAX_BODY_BYTES:
            raise ValueError("request too large")

        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except Exception as exc:
            raise ValueError(f"invalid json: {exc}") from exc

    def handle_spawn_pet(self):
        try:
            payload = self.read_json_body()
        except ValueError as exc:
            self.send_json({"ok": False, "error": str(exc)}, 400)
            return

        pet_json = payload.get("petJson") or {}
        spritesheet_data_url = payload.get("spritesheetDataUrl")
        dry_run = bool(payload.get("dryRun"))
        if not spritesheet_data_url:
            self.send_json({"ok": False, "error": "missing spritesheetDataUrl"}, 400)
            return

        display_name = str(pet_json.get("displayName") or pet_json.get("id") or "Custom Pet").strip()
        pet_id = slugify(pet_json.get("id") or display_name)
        package_dir = GENERATED_PETS_DIR / pet_id
        package_dir.mkdir(parents=True, exist_ok=True)

        try:
            sheet_bytes, mime = decode_data_url(spritesheet_data_url)
            extension = ".webp" if "webp" in (mime or "") else ".png"
            sheet_path = package_dir / f"spritesheet{extension}"
            sheet_path.write_bytes(sheet_bytes)
            pet_json = dict(pet_json)
            pet_json["id"] = pet_id
            pet_json["displayName"] = display_name or pet_id
            pet_json["spritesheetPath"] = sheet_path.name
            pet_json["spawnedAt"] = int(time.time())
            (package_dir / "pet.json").write_text(json.dumps(pet_json, indent=2), encoding="utf-8")
        except Exception as exc:
            self.send_json({"ok": False, "error": f"could not save pet package: {exc}"}, 500)
            return

        if dry_run:
            self.send_json(
                {
                    "ok": True,
                    "dryRun": True,
                    "packageDir": str(package_dir),
                    "spritesheetPath": str(sheet_path),
                    "petJsonPath": str(package_dir / "pet.json"),
                }
            )
            return

        try:
            pet_personality = str(pet_json.get("description") or pet_json.get("personality") or "").strip()
            spawn_args = [sys.executable, str(ROOT / "pet.py"), str(sheet_path), "--name", display_name or pet_id]
            if pet_personality:
                spawn_args += ["--personality", pet_personality]
            proc = subprocess.Popen(
                spawn_args,
                cwd=str(ROOT),
                close_fds=True,
                creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
            )
        except Exception as exc:
            self.send_json(
                {
                    "ok": False,
                    "error": f"saved package but could not spawn pet: {exc}",
                    "packageDir": str(package_dir),
                    "spritesheetPath": str(sheet_path),
                },
                500,
            )
            return

        self.send_json(
            {
                "ok": True,
                "pid": proc.pid,
                "packageDir": str(package_dir),
                "spritesheetPath": str(sheet_path),
                "petJsonPath": str(package_dir / "pet.json"),
            }
        )

    def handle_openai_image(self):
        try:
            payload = self.read_json_body()
        except ValueError as exc:
            self.send_json({"ok": False, "error": str(exc)}, 400)
            return

        prompt = (payload.get("prompt") or "").strip()
        stage = payload.get("stage") or "base"
        row_id = payload.get("rowId") or ""
        expected_frames = int(payload.get("expectedFrames") or 8)
        reference_image = payload.get("referenceImage")
        size = payload.get("size") or ("1024x1024" if stage == "base" else "1536x1024")
        api_key = os.environ.get("OPENAI_API_KEY")

        if not prompt:
            self.send_json({"ok": False, "error": "missing prompt"}, 400)
            return

        if not ENABLE_OPENAI or not api_key:
            self.send_json(
                {
                    "ok": False,
                    "code": "image_generation_paused",
                    "prompt": prompt,
                    "message": "Built-in image generation is paused while OpenAI is removed. Copy this prompt into your preferred image tool or import a row.",
                },
                409,
            )
            return

        try:
            if reference_image:
                ref_bytes, mime = decode_data_url(reference_image)
                files = [("image[]", "canonical-base.png", mime or "image/png", ref_bytes)]
                guide = make_layout_guide(row_id or "row", expected_frames)
                if guide:
                    files.append(("image[]", "layout-guide.png", "image/png", guide))
                fields = {
                    "model": IMAGE_MODEL,
                    "prompt": prompt,
                    "size": size,
                    "quality": QUALITY,
                    "output_format": "png",
                }
                result = openai_multipart_request("https://api.openai.com/v1/images/edits", fields, files, api_key)
            else:
                result = openai_json_request(
                    "https://api.openai.com/v1/images/generations",
                    {
                        "model": IMAGE_MODEL,
                        "prompt": prompt,
                        "size": size,
                        "quality": QUALITY,
                        "output_format": "png",
                    },
                    api_key,
                )
            image_b64 = extract_image_b64(result)
            if not image_b64:
                self.send_json({"ok": False, "error": "OpenAI response did not contain image data", "raw": result}, 502)
                return
            self.send_json({"ok": True, "stage": stage, "rowId": row_id, "imageBase64": image_b64})
        except urllib.error.HTTPError as exc:
            err_body = exc.read().decode("utf-8", errors="replace")
            self.send_json({"ok": False, "error": f"OpenAI HTTP {exc.code}", "details": err_body}, 502)
        except Exception as exc:
            self.send_json({"ok": False, "error": str(exc)}, 500)

    def handle_analyze_reference(self):
        try:
            payload = self.read_json_body()
        except ValueError as exc:
            self.send_json({"ok": False, "error": str(exc)}, 400)
            return

        reference_image = payload.get("referenceImage")
        source_name = (payload.get("sourceName") or "uploaded reference").strip()
        api_key = os.environ.get("OPENAI_API_KEY")

        if not reference_image:
            self.send_json({"ok": False, "error": "missing referenceImage"}, 400)
            return

        if not ENABLE_OPENAI or not api_key:
            self.send_json(
                {
                    "ok": False,
                    "code": "analysis_paused",
                    "message": "Automatic reference analysis is paused. The app will still use the uploaded image as the visual source of truth.",
                },
                409,
            )
            return

        prompt = (
            "Analyze this uploaded desktop-pet reference image. Return one concise paragraph, "
            "35 to 70 words, describing only the character identity for sprite generation: species/object type, "
            "body shape, face, colors, materials, accessories, asymmetry, important markings, and silhouette. "
            "Do not mention background, image quality, pose, camera, or animation instructions."
        )

        try:
            result = openai_json_request(
                "https://api.openai.com/v1/responses",
                {
                    "model": VISION_MODEL,
                    "input": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "input_text", "text": prompt},
                                {"type": "input_image", "image_url": reference_image},
                            ],
                        }
                    ],
                    "max_output_tokens": 180,
                },
                api_key,
            )
            analysis = extract_response_text(result)
            if not analysis:
                self.send_json({"ok": False, "error": "OpenAI response did not contain analysis text", "raw": result}, 502)
                return
            self.send_json({"ok": True, "sourceName": source_name, "analysis": analysis})
        except urllib.error.HTTPError as exc:
            err_body = exc.read().decode("utf-8", errors="replace")
            self.send_json({"ok": False, "error": f"OpenAI HTTP {exc.code}", "details": err_body}, 502)
        except Exception as exc:
            self.send_json({"ok": False, "error": str(exc)}, 500)


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PORT
    server = ThreadingHTTPServer(("127.0.0.1", port), PetStudioHandler)
    print(f"Pet Hatch Studio running at http://127.0.0.1:{port}/pet_studio.html")
    google_ready = bool(os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY"))
    print(f"Google pet brain key detected: {'yes' if google_ready else 'no'}")
    if not google_ready:
        print("Set GOOGLE_API_KEY or GEMINI_API_KEY before starting this server to enable pet chat and agent replies.")
    server.serve_forever()


if __name__ == "__main__":
    main()
