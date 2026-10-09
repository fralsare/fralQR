# fralQR — User Manual

fralQR is a desktop app for making scannable QR codes from a PDF menu (and for
turning images back into a PDF). This manual covers installation and every screen.

---

## 1. What fralQR does

- **PDF → QR codes** — hosts your PDF online and generates two print-ready QR codes.
- **Image(s) → PDF** — builds a multi-page PDF from photos/scans.
- **Help menu** — Donations and About.

It works on **Windows** and **Linux** and opens in its own window (no browser).

---

## 2. Installing

### 2.1 Windows
- **Installer (`.exe`)** — double-click, then click Next. Creates a Start-menu
  entry and a desktop shortcut.
- **Portable (`.exe`)** — no install; just double-click. Keep the file wherever
  you like (a USB drive works well).

### 2.2 Linux
- **AppImage**
  ```bash
  chmod +x fralQR-1.0.0-x86_64.AppImage
  ./fralQR-1.0.0-x86_64.AppImage
  ```
  (First run may prompt to "Extract and run" if FUSE is unavailable — allow it.)
- **`.deb`** (Debian, Ubuntu, Linux Mint…)
  ```bash
  sudo dpkg -i fralQR_1.0.0_amd64.deb
  # if you get a dependency error:
  sudo apt --fix-broken install
  ```
- **`.rpm`** (Fedora, RHEL, openSUSE…)
  ```bash
  sudo rpm -i fralQR-1.0.0-1.x86_64.rpm
  ```

### 2.3 From source
```bash
# Linux
./fralQR.sh
# or
python3 fralQR.py

# Windows
python fralQR.py          # (or double-click fralQR.bat)
```
Install Pillow only if you use the Image→PDF tab: `pip install -r requirements.txt`.

---

## 3. Tab 1 — PDF → QR Code (the main job)

**Step 1 — Choose the PDF.** Click **Choose PDF…** and pick your menu PDF
(e.g. `BohoAmigoMenu.pdf`).

**Step 2 — Choose the output folder.** This is where the QR codes and URLs are
saved. By default it is the folder the PDF is in. Click **Browse…** to change it.

**Step 3 — Generate.** Click **Generate QR codes**.

The status box at the bottom shows progress, e.g.:

```text
--- PDF -> QR ---
Hosted PDF at: https://files.catbox.moe/xxxxxx.pdf
Direct URL: https://files.catbox.moe/xxxxxx.pdf
Viewer URL: https://docs.google.com/viewer?url=...&embedded=true
Saved:
  /path/…_qr_direct.png
  /path/…_qr_viewer.png
  ...
```

**Step 4 — Read the result.** The window shows both QR codes side by side, with
buttons to **Copy** each URL and to **Open output folder**.

### What the two QR codes mean
- **Direct QR** (`…_qr_direct.png`) — points straight at the hosted PDF file.
- **Viewer QR** (`…_qr_viewer.png`) — points at a browser PDF *viewer* wrapping
  the PDF. **This is the one to print.** It opens faster and looks better on phones.

### Output files

| File | What it is |
|------|-----------|
| `…_qr_direct.png` | QR image (direct link) |
| `…_qr_viewer.png` | QR image (**viewer — print this**) |
| `…_hosted_url.txt` | the raw host URL |
| `…_viewer_url.txt` | the viewer URL |
| `…_QR_NOTES.md` | a short text summary |

### Printing tips
- Print the **viewer** QR at at least ~70×70 mm (about 3×3 in).
- Keep it high contrast (black on white) with a small white margin around it.
- Test-scan with a couple of different phones before printing all of them.

---

## 4. Tab 2 — Image(s) → PDF

Use this to turn photos/scans of a menu back into a single PDF (for example, to
re-host a menu you only have as images).

1. Click **Choose image(s)…** and select one or more images. They appear in the
   list (in filename order — name them `01.jpg, 02.jpg, …` if you want a specific
   page order).
2. Pick a **Page size**: A4 or Letter, portrait or landscape.
3. Set the **Output PDF path** (default: `menu_from_images.pdf` next to the first
   image). Click **Save As…** to change it.
4. Click **Create PDF from image(s)**. Each image becomes one page, scaled to fit
   and centered on a white page.

---

## 5. The Help menu

- **Help → Donations / Support** — opens the donation dialog (copy or open the
  PayPal / Razorpay links).
- **Help → About** — shows the version and a short description.

---

## 6. How the QR process works (the "why")

A QR code can only store a URL, not a file. So to share a PDF menu:

1. **Host** the PDF at a public URL.
2. **Wrap** it in a viewer URL (so phones render it nicely).
3. **Encode** each URL as a QR image.

fralQR does all three steps with one click.

---

## 7. Troubleshooting

**"HTTP 502 / 503 … from api.qrserver.com"**
A temporary problem on the QR service's side. The app already retries several
times automatically. If it still fails, click **Generate QR codes** again — the
PDF is already hosted, so this is safe to repeat.

**Window does not open on Linux ("No module named tkinter")**
```bash
# Debian / Ubuntu
sudo apt install python3-tk
# Fedora
sudo dnf install python3-tkinter
```

**"No module named PIL" on the Image→PDF tab**
```bash
pip install -r requirements.txt
```
(The QR tab works fine without Pillow.)

**No internet**
The app needs the internet to host the PDF and fetch the QR images. It cannot
generate QRs offline.

**The hosted PDF URL stops working later**
The public host (Catbox.moe) keeps files for a long time but is not a permanent
CDN. If a menu link ever dies, just re-run the QR process to get a fresh hosted
URL and new QR codes.

**QR will not scan**
Make it bigger and higher-contrast; avoid photo filters, curved surfaces, and
glossy glare. The viewer QR with its quiet zone is the most reliable.

---

## 8. Security & privacy

- All connections are **HTTPS-only**.
- The PDF is uploaded to a **public** host — anyone with the URL (or a scan of
  the QR) can open it. Only use this for content you intend to share publicly.
- There is **no account**, no tracking, and no data collection by fralQR itself.

---

## 9. System requirements

- **Windows:** Windows 10/11 (64-bit), Python 3.10+ (bundled in the release builds).
- **Linux:** any modern 64-bit distribution, Python 3.10+ with tkinter.
- **Pillow** for the Image→PDF tab.
- An internet connection.
