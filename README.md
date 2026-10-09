# fralQR

<!--
  GitHub "About" box metadata (set it via the "..." / gear on the right sidebar
  of the repo page). Paste the two values below into those fields.

  Description:
    Turn a PDF menu into print-ready QR codes. Feed it a PDF, print the codes,
    and customers scan to view the menu in their browser. Windows + Linux
    desktop app.

  Topics (space- or comma-separated, lowercase, no spaces inside a tag):
    qr-code pdf python tkinter desktop-app cross-platform menu restaurant
    image-to-pdf print gui standalone pyinstaller
-->

**Feed a PDF, get scannable menu QR codes.**

fralQR is a tiny, single-purpose, cross-platform desktop app (Windows + Linux)
that opens in its own window and uses **no external browser**. You hand it a PDF;
it hosts the PDF and generates two print-ready QR codes that open the menu on
any phone.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg) ![License](https://img.shields.io/badge/License-MIT-green.svg) ![Platforms](https://img.shields.io/badge/Platforms-Windows%20%7C%20Linux-lightgrey.svg)

> A QR code only stores a URL. To make a phone show your menu, the PDF must be
> hosted at a public URL first — fralQR handles that whole process for you.

## Features

- **PDF → QR codes** — uploads your PDF to a public host, then generates **two** QR codes:
  - a **direct** QR (points straight at the PDF), and
  - a **viewer** QR (recommended — wraps the PDF so phones open it in a smooth in-browser PDF viewer).
- **Image(s) → PDF** — turn one or more photos/scans into a single multi-page PDF (A4 or Letter) — handy for rebuilding a PDF from menu photos.
- **Cross-platform GUI** (tkinter) — Windows + Linux, own window, no browser dependency.
- **Resilient** — automatically retries on transient network errors (HTTP 5xx / 429) from the QR service.
- **In-app Donations** — `Help → Donations / Support`.
- Ships as: **`.AppImage`**, **`.deb`**, **`.rpm`**, **Windows installer `.exe`**, and **Windows portable `.exe`**.

## Downloads

Release builds are on [GitHub Releases](https://github.com/fralsare/fralQR/releases). Pick the file for your platform:

| Platform | Files |
|----------|-------|
| **Linux** | `fralQR-<ver>-amd64.AppImage` (any distro) · `fralQR_<ver>_amd64.deb` (Debian/Ubuntu) · `fralQR-<ver>-1.x86_64.rpm` (Fedora/RHEL/openSUSE) |
| **Windows** | `fralQR-Setup-<ver>.exe` (installer) · `fralQR-<ver>-portable.exe` (portable, no install) |

The AppImage and the portable `.exe` need no installation. The `.deb` / `.rpm` / installer also add a **Start menu** entry and a desktop icon.

## Quick start

### Run from a release build

1. Download the latest release for your platform below.
2. **Linux**
   - **AppImage** → make it executable (`chmod +x fralQR-*.AppImage`) and run it, **or**
   - **`.deb`** (Debian/Ubuntu) → `sudo dpkg -i fralQR_*.deb`
   - **`.rpm`** (Fedora/RHEL/openSUSE) → `sudo rpm -i fralQR-*.rpm`
3. **Windows**
   - **Installer `.exe`** → double-click and follow the wizard, **or**
   - **Portable `.exe`** → just double-click to run (no install).
4. The app opens in its own window. Go to the **PDF → QR Code** tab.

### Run from source

Requirements: Python 3.10+ (with tkinter) and, for the image→PDF tab, Pillow.

- **Linux:** `./fralQR.sh`
- **Windows:** double-click `fralQR.bat` (or `python fralQR.py`)

```bash
# Only if you use the Image->PDF tab:
pip install -r requirements.txt
```

## Using the app

### Tab 1 — PDF → QR Code
1. **Choose PDF…** → select your menu PDF.
2. Set the **Output folder** (defaults to the PDF's folder).
3. Click **Generate QR codes**.
4. When it finishes you'll see both QR codes in the window, plus these files in the output folder:
   - `…_qr_direct.png` — direct-link QR
   - `…_qr_viewer.png` — **viewer QR (print this one)**
   - `…_hosted_url.txt`, `…_viewer_url.txt` — the two URLs
   - `…_QR_NOTES.md` — a short notes file

👉 **Print the `_qr_viewer.png`** — it reliably opens the menu on any phone.
See [MANUAL.md](MANUAL.md) for the full walkthrough.

### Tab 2 — Image(s) → PDF
1. **Choose image(s)…** → select one or more menu photos.
2. Pick a **Page size** (A4 / Letter, portrait / landscape).
3. Set the **Output PDF path**.
4. Click **Create PDF from image(s)**.

### Menu
- **Help → Donations / Support** — show the in-app donation dialog.
- **Help → About** — version and info.

## How it works (the QR process)
1. Your PDF is uploaded to a public host (Catbox.moe) → you get a `https://….pdf` URL.
2. Two URLs are built:
   - **direct** = that host URL;
   - **viewer** = `https://docs.google.com/viewer?url=<host URL>&embedded=true`.
3. Each URL is turned into a QR PNG (600×600, high error-correction) via the `api.qrserver.com` service.
4. Everything is saved to your output folder and shown in the window.

## Requirements
- Python 3.10+ with **tkinter** (included with most installs; on some Linux you may need `python3-tk`).
- **Pillow** — only for the Image→PDF tab.
- Internet access (the app hosts the PDF and fetches QR images online).

## 🙏 Support open-source tool development

Your donation keeps this project maintained and funds new open-source projects,
while supporting my CyberSecurity studies. Even a small amount makes a real
difference. Thank you for supporting independent open-source work!

| Method | Link |
|--------|------|
| **PayPal** | [paypal.com/ncp/payment/KKFBWQP97XUCN](https://paypal.com/ncp/payment/KKFBWQP97XUCN) |
| **Razorpay** | [rzp.io/rzp/TdksERz](https://rzp.io/rzp/TdksERz) |

You can also open this any time from the app: **Help → Donations / Support**.
More at [SUPPORT.md](SUPPORT.md).

## Troubleshooting
- **HTTP 502 / 503 from the QR service** — usually temporary. The app already retries a few times; if it still fails, just click **Generate QR codes** again. Your PDF is already hosted, so no data is lost.
- **No tkinter** (Linux) — `sudo apt install python3-tk` (Debian/Ubuntu) or `sudo dnf install python3-tkinter` (Fedora).
- **Image→PDF tab errors** — install Pillow: `pip install -r requirements.txt`.
- Full details in [MANUAL.md](MANUAL.md).

## Security & privacy
- All network calls are **HTTPS-only**.
- Your PDF is uploaded to a **public** host (Catbox.moe) so anyone with the QR/URL can open it — that's the point, but only share URLs you intend to make public.
- No account, no data collection, no analytics.

## Building from source

Prefer to build the binaries yourself? Everything lives in [`packaging/`](packaging/):

- **Linux** (`.deb`, `.rpm`, `.AppImage`): `bash packaging/build_linux.sh` — builds a self-contained PyInstaller bundle, then packages it. Needs `python3-venv`, `dpkg-deb`, and `curl`; `rpmbuild` is optional.
- **Windows** (installer + portable `.exe`): on a Windows machine with Python 3.10+ and [Inno Setup 6](https://jrsoftware.org/isdl.php), run `packaging\build_windows.bat`.
- **Icons**: `python packaging/make_icon.py` regenerates `packaging/icon.png` and `icon.ico`.

[GitHub Actions](.github/workflows/build.yml) builds all five artifacts automatically on every release tag, so you can also just tag a release and download the binaries.

## License
MIT — see [LICENSE](LICENSE).
