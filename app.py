import os
import uuid
import json
from datetime import datetime
from flask import Flask, request, render_template, redirect, url_for, jsonify, send_from_directory, abort
from werkzeug.utils import secure_filename
import qrcode
from PIL import Image
import io
import base64

app = Flask(__name__)
app.secret_key = os.urandom(24)

# ── Config ──────────────────────────────────────────────────────────────
BASE_DIR       = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER  = os.path.join(BASE_DIR, "static", "uploads")
QR_FOLDER      = os.path.join(BASE_DIR, "static", "qrcodes")
DB_FILE        = os.path.join(BASE_DIR, "certificates.json")
ALLOWED_EXT    = {"png", "jpg", "jpeg", "webp"}
MAX_SIZE_MB    = 5
COMPANY_NAME   = "OceanX"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_SIZE_MB * 1024 * 1024

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(QR_FOLDER,     exist_ok=True)

# ── Tiny JSON "database" ─────────────────────────────────────────────────
def load_db():
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE) as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ── Helpers ──────────────────────────────────────────────────────────────
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT

def is_real_image(file_storage):
    """Verify bytes are actually an image (not just a renamed file)."""
    try:
        file_storage.stream.seek(0)
        img = Image.open(file_storage.stream)
        img.verify()
        file_storage.stream.seek(0)
        return True
    except Exception:
        return False

def generate_qr(url: str, token: str) -> str:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#1a1a2e", back_color="white")
    filename = f"qr_{token}.png"
    img.save(os.path.join(QR_FOLDER, filename))
    return filename

# ── Routes ───────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html", company=COMPANY_NAME)


@app.route("/upload", methods=["POST"])
def upload():
    errors = []

    # --- form fields ---
    candidate_name = request.form.get("candidate_name", "").strip()
    pnr_number     = request.form.get("pnr_number",     "").strip()

    if not candidate_name:
        errors.append("Candidate name is required.")
    if not pnr_number:
        errors.append("PNR number is required.")

    # --- file ---
    file = request.files.get("certificate")
    if not file or file.filename == "":
        errors.append("Certificate image is required.")
    elif not allowed_file(file.filename):
        errors.append("Only PNG, JPG, JPEG, or WEBP images are allowed.")
    elif not is_real_image(file):
        errors.append("Uploaded file is not a valid image.")

    if errors:
        return render_template("index.html", company=COMPANY_NAME, errors=errors,
                               form={"candidate_name": candidate_name, "pnr_number": pnr_number})

    # --- uniqueness: one token per PNR ---
    db = load_db()
    if pnr_number in db:
        token = db[pnr_number]["token"]
    else:
        token = uuid.uuid4().hex

    # --- save image ---
    ext      = secure_filename(file.filename).rsplit(".", 1)[1].lower()
    img_name = f"cert_{token}.{ext}"
    file.save(os.path.join(UPLOAD_FOLDER, img_name))

    # --- verification URL ---
    verify_url = url_for("verify", token=token, _external=True)
    # --- QR code ---
    qr_filename = generate_qr(verify_url, token)

    # --- persist ---
    db[pnr_number] = {
        "token":          token,
        "candidate_name": candidate_name,
        "pnr_number":     pnr_number,
        "image":          img_name,
        "qr":             qr_filename,
        "verify_url":     verify_url,
        "created_at":     datetime.utcnow().isoformat(),
    }
    save_db(db)

    return render_template("result.html",
                           company=COMPANY_NAME,
                           record=db[pnr_number],
                           qr_url=url_for("static", filename=f"qrcodes/{qr_filename}"))


@app.route("/verify/<token>")
def verify(token):
    db = load_db()
    record = next((r for r in db.values() if r["token"] == token), None)
    if not record:
        abort(404)
    return render_template("verify.html", company=COMPANY_NAME, record=record)


@app.route("/download/qr/<token>")
def download_qr(token):
    db    = load_db()
    record = next((r for r in db.values() if r["token"] == token), None)
    if not record:
        abort(404)
    return send_from_directory(QR_FOLDER, record["qr"], as_attachment=True,
                               download_name=f"QR_{record['pnr_number']}.png")


@app.errorhandler(404)
def not_found(e):
    return render_template("404.html", company=COMPANY_NAME), 404


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
