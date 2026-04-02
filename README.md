# CertifyPro — Certificate QR Verification System

A Flask web application that lets you upload a certificate image, register candidate details, and instantly generate a QR code linked to a tamper-evident public verification page.

---

## Folder Structure

```
cert_verifier/
├── app.py                  # Flask backend (all routes + logic)
├── requirements.txt        # Python dependencies
├── certificates.json       # Auto-created JSON "database"
├── templates/
│   ├── base.html           # Shared layout
│   ├── index.html          # Upload form (home page)
│   ├── result.html         # QR code display page
│   ├── verify.html         # Public verification page (scanned from QR)
│   └── 404.html            # Not-found page
└── static/
    ├── css/
    │   └── style.css       # All styles
    ├── uploads/            # Saved certificate images
    └── qrcodes/            # Generated QR code PNGs
```

---

## Quick Start

### 1. Clone / unzip the project

```bash
cd cert_verifier
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the development server

```bash
python app.py
```

Open your browser at **http://localhost:5000**

---

## How It Works

| Step | What happens |
|------|--------------|
| User uploads certificate + fills form | Flask validates image bytes with Pillow |
| Unique token generated via `uuid4()` | One token per PNR (idempotent) |
| QR code created with `qrcode` library | Encodes `http://localhost:5000/verify/<token>` |
| Result page shows QR | User can download the PNG |
| Anyone scans the QR | Opens `/verify/<token>` showing cert, name, PNR, stamp |

---

## Configuration (in `app.py`)

| Variable | Default | Description |
|----------|---------|-------------|
| `COMPANY_NAME` | `CertifyPro Inc.` | Shown on all pages |
| `MAX_SIZE_MB` | `5` | Max upload size |
| `ALLOWED_EXT` | `png jpg jpeg webp` | Accepted image types |

---

## Production Notes

- Replace `certificates.json` with a proper database (SQLite → PostgreSQL).
- Set `SECRET_KEY` from an environment variable instead of `os.urandom(24)`.
- Serve via **Gunicorn** behind **Nginx**.
- Add HTTPS so QR codes resolve to `https://` URLs.
