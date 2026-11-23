"""Local HTTP bridge around the unchanged supplied Keras model.

This file is an added integration layer, not a replacement for the source notebook.
The default prediction path preserves the notebook's preprocessing.
"""
from __future__ import annotations

import argparse
import io
import json
import logging
import os
from pathlib import Path
import threading
import time
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit, unquote
import uuid
import warnings

ROOT = Path(__file__).resolve().parent.parent
MAX_BYTES = 10 * 1024 * 1024
MAX_PIXELS = 20_000_000


class InvalidImage(ValueError):
    pass


class Predictor:
    def __init__(self, model_path: Path, classes_path: Path, mode: str = "notebook"):
        os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
        import numpy as np
        import tf_keras as keras
        from PIL import Image
        Image.MAX_IMAGE_PIXELS = MAX_PIXELS
        self.np = np
        self.keras = keras
        self.mode = mode
        self.labels = json.loads(classes_path.read_text(encoding="utf-8-sig"))
        if len(self.labels) != 36 or len(set(self.labels)) != 36:
            raise ValueError("Expected 36 unique class labels.")
        self.model = keras.models.load_model(str(model_path), compile=False)
        if tuple(self.model.input_shape[1:]) != (256, 256, 3) or self.model.output_shape[-1] != len(self.labels):
            raise ValueError("The supplied model shape and class labels do not match.")
        self.lock = threading.Lock()

    def predict(self, content: bytes) -> dict:
        from PIL import Image, ImageOps, UnidentifiedImageError
        np = self.np
        started = time.perf_counter()
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", Image.DecompressionBombWarning)
                with Image.open(io.BytesIO(content)) as source:
                    if source.format not in {"JPEG", "PNG", "WEBP"}:
                        raise InvalidImage("Choose a JPG, PNG or WebP image.")
                    width, height = source.size
                    if width * height > MAX_PIXELS:
                        raise InvalidImage("Choose an image with no more than 20 million pixels.")
                    source.load()
                    image = ImageOps.exif_transpose(source).convert("RGB")
            if self.mode == "notebook":
                # Reproduce the source Tkinter path: thumbnail, resize, then divide by 255.
                image.thumbnail((300, 300))
                image = image.resize((256, 256))
                array = np.asarray(image, dtype=np.float32) / 255.0
            else:
                image = image.resize((256, 256), resample=Image.Resampling.NEAREST)
                array = self.keras.applications.vgg19.preprocess_input(np.asarray(image, dtype=np.float32).copy())
        except InvalidImage:
            raise
        except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
            raise InvalidImage("This image cannot be read. Choose a valid JPG, PNG or WebP file.") from exc
        with self.lock:
            # Direct call avoids creating a tf.data worker pool for one image.
            scores = np.asarray(self.model(np.expand_dims(array, 0), training=False))[0]
        if scores.shape != (len(self.labels),) or not np.all(np.isfinite(scores)) or np.any(scores < 0) or np.any(scores > 1):
            raise RuntimeError("The model returned invalid class scores.")
        ranking = np.argsort(scores)[::-1][:3]
        predictions = []
        for index in ranking:
            label = self.labels[int(index)]
            crop, condition = label.split("___", 1)
            predictions.append({"class_index": int(index), "label": label, "crop": crop,
                                "condition": condition, "score": float(scores[index])})
        return {"id": str(uuid.uuid4()), "created_at": datetime.now(timezone.utc).isoformat(),
                "predictions": predictions, "elapsed_ms": round((time.perf_counter() - started) * 1000),
                "model": "VGG19 plant classifier", "preprocessing": self.mode,
                "image": {"width": width, "height": height},
                "warning": "Uncalibrated model scores. Independent accuracy is not established. Class order reconstructed from sorted training folders."}


def make_handler(predictor: Predictor, directory: Path, port: int, extra_origins: list[str]):
    directory = directory.resolve()
    allowed_origins = {f"http://127.0.0.1:{port}", f"http://localhost:{port}", *extra_origins}
    allowed_hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(directory), **kwargs)

        def end_headers(self):
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("X-Frame-Options", "DENY")
            if self.path.startswith("/api/"):
                self.send_header("Cache-Control", "no-store")
            origin = self.headers.get("Origin")
            if origin in allowed_origins:
                self.send_header("Access-Control-Allow-Origin", origin)
                self.send_header("Vary", "Origin")
            super().end_headers()

        def json_response(self, status: int, body: dict):
            payload = json.dumps(body, allow_nan=False).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def allowed(self):
            if self.headers.get("Host", "") not in allowed_hosts:
                self.json_response(403, {"error": "Use the printed localhost URL."})
                return False
            origin = self.headers.get("Origin")
            if origin and origin not in allowed_origins:
                self.json_response(403, {"error": "This frontend origin is not allowed."})
                return False
            return True

        def do_OPTIONS(self):
            if not self.allowed():
                return
            self.send_response(204)
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Max-Age", "600")
            self.end_headers()

        def do_GET(self):
            if not self.allowed():
                return
            path = urlsplit(self.path).path
            if path == "/api/health":
                self.json_response(200, {"status": "ready", "model": "VGG19", "class_count": len(predictor.labels),
                                         "preprocessing": predictor.mode})
            elif path == "/api/classes":
                self.json_response(200, {"classes": predictor.labels,
                                         "mapping_source": "Sorted Train directory names from the supplied archive"})
            elif path.startswith("/api/"):
                self.json_response(404, {"error": "API endpoint not found."})
            else:
                target = (directory / unquote(path).lstrip("/")).resolve()
                if not target.is_relative_to(directory) or any(p.startswith(".") for p in target.relative_to(directory).parts):
                    self.send_error(404)
                    return
                if path == "/":
                    self.path = "/index.html"
                super().do_GET()

        def do_POST(self):
            if not self.allowed():
                self.close_connection = True
                return
            if urlsplit(self.path).path != "/api/predict":
                self.json_response(404, {"error": "API endpoint not found."})
                self.close_connection = True
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                length = -1
            if length <= 0 or self.headers.get("Transfer-Encoding"):
                self.json_response(400, {"error": "Send one image with a valid Content-Length."})
                self.close_connection = True
                return
            if length > MAX_BYTES:
                self.json_response(413, {"error": "Choose an image smaller than 10 MB."})
                self.close_connection = True
                return
            if self.headers.get_content_type() not in {"image/jpeg", "image/png", "image/webp"}:
                self.json_response(415, {"error": "Choose a JPG, PNG or WebP image."})
                self.close_connection = True
                return
            try:
                self.connection.settimeout(30)
                content = self.rfile.read(length)
                if len(content) != length:
                    raise InvalidImage("The upload was incomplete. Try again.")
                result = predictor.predict(content)
                self.json_response(200, result)
            except InvalidImage as exc:
                self.json_response(422, {"error": str(exc)})
            except (TimeoutError, ConnectionError, BrokenPipeError):
                self.close_connection = True
            except Exception:
                logging.exception("Prediction failed")
                self.json_response(500, {"error": "The model could not process this image. Try another photo."})

        def list_directory(self, path):
            self.send_error(404)
            return None

    return Handler


def main():
    parser = argparse.ArgumentParser(description="Serve the Plant Disease Lab frontend and original model locally.")
    parser.add_argument("--model", type=Path, default=ROOT / "original" / "best_model.h5")
    parser.add_argument("--classes", type=Path, default=ROOT / "backend" / "classes.json")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--allow-origin", action="append", default=[])
    parser.add_argument("--preprocessing", choices=["notebook", "vgg19"], default="notebook")
    args = parser.parse_args()
    if not (ROOT / "dist" / "index.html").is_file():
        parser.error("Built frontend missing. Run npm install and npm run build first.")
    if not args.model.is_file():
        parser.error("Model file missing. Place the original best_model.h5 in original/ or pass --model.")
    print("Loading the supplied model. Original files will not be modified.", flush=True)
    predictor = Predictor(args.model, args.classes, args.preprocessing)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(predictor, ROOT / "dist", args.port, args.allow_origin))
    print(f"Plant Disease Lab ready at http://127.0.0.1:{args.port}", flush=True)
    print(f"Preprocessing: {predictor.mode}. Press Ctrl+C to stop.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Plant Disease Lab.", flush=True)
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
