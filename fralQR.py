#!/usr/bin/env python3
"""
fralQR  --  Feed a PDF, get QR codes.  (plus: build a PDF from image(s))

A tiny, single-purpose, cross-platform desktop app (Windows + Linux).
It opens in its own window and uses NO external browser.

Core idea (what "the QR code process" means):
  A QR code only stores a URL. To make a phone show a menu, the PDF must be
  hosted on a public URL first, then a QR code is generated that points to it.

So this app does two focused jobs:
  1. PDF -> QR codes   : upload the PDF to a public host, then generate two
                         QR codes (a "direct" link and a browser "viewer" link).
  2. Image(s) -> PDF   : turn one or more images into a single PDF (via Pillow).

Only the Python standard library + Pillow (for the image->PDF job) are used.
No external GUI toolkit is required (tkinter ships with Python).
"""

import os
import io
import uuid
import queue
import contextlib
import platform
import subprocess
import threading
import time
import http.client
import urllib.parse
import webbrowser

import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk

# --------------------------------------------------------------------------- #
#  Core (non-GUI) helpers  --  these are the actual "process" the app runs     #
# --------------------------------------------------------------------------- #

QR_API = "https://api.qrserver.com/v1/create-qr-code/"
CATBOX_API = "https://catbox.moe/user/api.php"

APP_NAME = "fralQR"
APP_VERSION = "1.0.0"
APP_TAGLINE = "Feed a PDF, get scannable menu QR codes (plus: build a PDF from image(s))."
PAYPAL_URL = "https://paypal.com/ncp/payment/KKFBWQP97XUCN"
RAZORPAY_URL = "https://rzp.io/rzp/TdksERz"
DONATION_TEXT = (
    "Your donation keeps this project maintained and funds new open-source "
    "projects, while supporting my CyberSecurity studies. Even a small amount "
    "makes a real difference. Thank you for supporting independent open-source "
    "work!"
)

# Page sizes at 150 DPI (width, height) in pixels, for the image->PDF job.
PAGE_SIZES = {
    "A4 (portrait)":      (1240, 1754),
    "A4 (landscape)":     (1754, 1240),
    "Letter (portrait)":  (1275, 1755),
    "Letter (landscape)": (1755, 1275),
}


def build_multipart(fields, files):
    """Build a multipart/form-data body.

    fields: {name: value}
    files:  {field: (filename, bytes, content-type)}
    returns (body_bytes, content_type_header)
    """
    boundary = uuid.uuid4().hex
    out = io.BytesIO()

    def w(s):
        out.write(s.encode() if isinstance(s, str) else s)

    for name, value in (fields or {}).items():
        w(f'--{boundary}\r\n'
          f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
          f'{value}\r\n')
    for name, (fname, data, ctype) in files.items():
        w(f'--{boundary}\r\n'
          f'Content-Disposition: form-data; name="{name}"; filename="{fname}"\r\n')
        w(f'Content-Type: {ctype}\r\n\r\n')
        w(data)
        w("\r\n")
    w(f'--{boundary}--\r\n')
    return out.getvalue(), f"multipart/form-data; boundary={boundary}"


def _split_https_url(url):
    """Split an https URL into (host, path-with-query). Only https is allowed."""
    parts = urllib.parse.urlsplit(url)
    if parts.scheme != "https" or not parts.hostname:
        raise ValueError(f"Only https URLs are supported, got: {url!r}")
    path = parts.path or "/"
    if parts.query:
        path += "?" + parts.query
    return parts.hostname, path


class _TransientHTTPError(Exception):
    """A retryable HTTP status (5xx / 429) returned by the server."""
    def __init__(self, status, host, path):
        self.status = status
        super().__init__(f"HTTP {status} from {host}{path}")


def _https_request(method, host, path, body=None, headers=None,
                   timeout=60, retries=2):
    """Perform an explicit HTTPS request and return the response body (bytes).

    Retries on transient network errors AND on retryable HTTP statuses
    (5xx / 429) -- e.g. a 502 "Bad Gateway" from a busy public service.
    Always sets a User-Agent (http.client does not send one by default).
    """
    hdrs = {"User-Agent": "fralQR/1.0", "Connection": "close"}
    hdrs.update(headers or {})
    last = None
    for attempt in range(retries + 1):
        try:
            conn = http.client.HTTPSConnection(host, timeout=timeout)
            try:
                conn.request(method, path, body=body, headers=hdrs)
                resp = conn.getresponse()
                data = resp.read()
                status = resp.status
                if 200 <= status < 300:
                    return data
                if status == 429 or status >= 500:      # retryable
                    raise _TransientHTTPError(status, host, path)
                raise RuntimeError(f"HTTP {status} from {host}{path}")
            finally:
                conn.close()
        except (http.client.HTTPException, OSError, _TransientHTTPError) as e:
            last = e
            if attempt < retries:
                time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(
        f"Request to {host}{path} failed after {retries + 1} tries: {last}") from last


def host_pdf(pdf_path, log=print):
    """Upload a PDF to a public host and return its URL."""
    try:
        with open(pdf_path, "rb") as f:
            data = f.read()
    except OSError as e:
        raise RuntimeError(f"Could not read PDF {pdf_path}: {e}") from e
    host, path = _split_https_url(CATBOX_API)
    payload, ctype = build_multipart(
        {"reqtype": "fileupload"},
        {"fileToUpload": (os.path.basename(pdf_path), data, "application/pdf")},
    )
    body = _https_request("POST", host, path, body=payload,
                          headers={"Content-Type": ctype}, timeout=120)
    url = body.decode().strip()
    if not url.startswith("http"):
        raise RuntimeError(f"Hosting failed (got no URL): {url!r}")
    log(f"Hosted PDF at: {url}")
    return url


def build_viewer_url(raw_url):
    """Wrap a raw PDF URL so phones open it in a browser PDF viewer."""
    enc = urllib.parse.quote(raw_url)
    return f"https://docs.google.com/viewer?url={enc}&embedded=true"


def fetch_qr(url, size=600, level="H", margin=15):
    """Fetch a QR code PNG (as bytes) for the given URL from the QR API.

    Retries on transient server errors (5xx / 429), since public QR services
    occasionally blip.
    """
    q = (f"size={size}x{size}&data={urllib.parse.quote(url)}"
         f"&errorcorrectionlevel={level}&margin={margin}")
    host, path = _split_https_url(QR_API + "?" + q)
    try:
        png = _https_request("GET", host, path, timeout=60, retries=3)
    except RuntimeError as e:
        raise RuntimeError(
            f"Could not fetch the QR image: {e}\n\n"
            "This is usually a temporary problem on the QR service's side.\n"
            "Your PDF is already hosted -- just click 'Generate QR codes' again.") from e
    if png[:4] != b"\x89PNG":
        raise RuntimeError("QR service did not return a PNG image")
    return png


def images_to_pdf(image_paths, out_pdf, page_key="A4 (portrait)", dpi=150, log=print):
    """Write one or more images into a single PDF, one image per page.

    Each image is scaled (preserving aspect ratio) to fit the chosen page and
    centered on a white page. Uses Pillow.
    """
    from PIL import Image

    pw, ph = PAGE_SIZES[page_key]
    pages = []
    for p in image_paths:
        im = Image.open(p).convert("RGB")
        scale = min(pw / im.width, ph / im.height)   # fit inside page
        nw, nh = max(1, int(im.width * scale)), max(1, int(im.height * scale))
        im = im.resize((nw, nh), Image.Resampling.LANCZOS)
        page = Image.new("RGB", (pw, ph), "white")
        page.paste(im, ((pw - nw) // 2, (ph - nh) // 2))
        pages.append(page)
        log(f"Added page from: {os.path.basename(p)}")

    pages[0].save(out_pdf, format="PDF", save_all=True,
                  append_images=pages[1:], resolution=float(dpi))
    log(f"PDF written: {out_pdf}")
    return out_pdf


def open_in_file_manager(path):
    """Open a folder (or file) with the OS file manager. Not a web browser."""
    try:
        if platform.system() == "Windows":
            # `start` opens the default program; the empty string is the title.
            subprocess.Popen(["cmd", "/c", "start", "", path])
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    except OSError as e:
        print(f"Could not open file manager: {e}")


# --------------------------------------------------------------------------- #
#  GUI                                                                        #
# --------------------------------------------------------------------------- #

class FralQRApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} v{APP_VERSION}  -  PDF -> QR codes  (+ Image -> PDF)")
        self.geometry("640x760")
        self.minsize(600, 640)
        self.configure(padx=10, pady=8)

        # keep-alive references so tk images are not garbage collected
        self.qr_viewer_img = None
        self.qr_direct_img = None

        self._job_running = False
        self._q = queue.Queue()

        self._build_ui()
        self._build_menu()
        self.after(100, self._poll_queue)

    # ---- UI construction ------------------------------------------------- #
    def _build_ui(self):
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True)

        self.tab_qr = tk.Frame(self.nb)
        self.tab_pdf = tk.Frame(self.nb)
        self.nb.add(self.tab_qr, text="  PDF  ->  QR Code  ")
        self.nb.add(self.tab_pdf, text="  Image(s)  ->  PDF  ")

        self._build_qr_tab()
        self._build_pdf_tab()

        ttk.Label(self, text="Status:").pack(anchor="w", pady=(10, 0))
        self.logbox = tk.Text(self, height=8, state="disabled", wrap="word",
                              font=("TkDefaultFont", 9))
        self.logbox.pack(fill="x")

    def _build_qr_tab(self):
        t = self.tab_qr

        tk.Label(t, text="Step 1 - choose a PDF:",
                 font=("TkDefaultFont", 10, "bold")).pack(anchor="w", padx=6, pady=4)
        row = tk.Frame(t)
        row.pack(fill="x")
        self.qr_file_var = tk.StringVar()

        def pick_pdf():
            p = filedialog.askopenfilename(
                title="Choose a PDF to share",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")])
            if p:
                self.qr_file_var.set(p)
                if not self.qr_out_var.get():
                    self.qr_out_var.set(os.path.dirname(p))
        tk.Button(row, text="Choose PDF...", command=pick_pdf).pack(side="left")
        tk.Entry(row, textvariable=self.qr_file_var).pack(
            side="left", fill="x", expand=True, padx=6)

        tk.Label(t, text="Output folder (where QR codes are saved):",
                 font=("TkDefaultFont", 10, "bold")).pack(anchor="w", padx=6, pady=4)
        row2 = tk.Frame(t)
        row2.pack(fill="x")
        self.qr_out_var = tk.StringVar()
        tk.Entry(row2, textvariable=self.qr_out_var).pack(side="left", fill="x", expand=True)
        tk.Button(row2, text="Browse...",
                  command=lambda: self._pick_folder(self.qr_out_var)).pack(side="left", padx=6)

        tk.Button(t, text="Generate QR codes",
                  command=self.on_generate_qr).pack(pady=12)

        # result area (populated after a job finishes)
        self.qr_result = tk.Frame(t)
        self.qr_result.pack(fill="x", pady=4)
        self.qr_urls_frame = tk.Frame(t)
        self.qr_urls_frame.pack(fill="x", pady=4)

    def _build_pdf_tab(self):
        t = self.tab_pdf

        tk.Label(t, text="Step 1 - choose image(s):",
                 font=("TkDefaultFont", 10, "bold")).pack(anchor="w", padx=6, pady=4)
        row = tk.Frame(t)
        row.pack(fill="x")
        self.img_var = tk.StringVar()

        def pick_imgs():
            paths = filedialog.askopenfilenames(
                title="Choose image(s) to turn into a PDF",
                filetypes=[("Images", "*.png *.jpg *.jpeg *.gif *.bmp *.webp"),
                           ("All files", "*.*")])
            if paths:
                paths = sorted(paths, key=os.path.basename)
                self.img_var.set("\n".join(paths))
                first_dir = os.path.dirname(paths[0])
                if not self.pdf_out_var.get():
                    self.pdf_out_var.set(os.path.join(first_dir, "menu_from_images.pdf"))
        tk.Button(row, text="Choose image(s)...", command=pick_imgs).pack(side="left")
        self.img_list = tk.Text(row, height=3, width=50, state="disabled")
        self.img_list.pack(side="left", fill="x", expand=True, padx=6)

        def refresh_img_list(*_):
            self.img_list.configure(state="normal")
            self.img_list.delete("1.0", "end")
            self.img_list.insert("1.0", self.img_var.get())
            self.img_list.configure(state="disabled")
        self.img_var.trace_add("write", refresh_img_list)

        tk.Label(t, text="Output PDF path:",
                 font=("TkDefaultFont", 10, "bold")).pack(anchor="w", padx=6, pady=4)
        row2 = tk.Frame(t)
        row2.pack(fill="x")
        self.pdf_out_var = tk.StringVar()
        tk.Entry(row2, textvariable=self.pdf_out_var).pack(side="left", fill="x", expand=True)

        def save_as():
            p = filedialog.asksaveasfilename(
                title="Save PDF as...", defaultextension=".pdf",
                initialfile="menu_from_images.pdf",
                filetypes=[("PDF files", "*.pdf")])
            if p:
                self.pdf_out_var.set(p)
        tk.Button(row2, text="Save As...", command=save_as).pack(side="left", padx=6)

        tk.Label(t, text="Page size:",
                 font=("TkDefaultFont", 10, "bold")).pack(anchor="w", padx=6, pady=4)
        self.page_var = tk.StringVar(value="A4 (portrait)")
        ttk.Combobox(t, textvariable=self.page_var, values=list(PAGE_SIZES.keys()),
                     state="readonly", width=22).pack(anchor="w")

        tk.Button(t, text="Create PDF from image(s)",
                  command=self.on_create_pdf).pack(pady=12)

    # ---- menu: Help (Donate / About) ------------------------------------- #
    def _build_menu(self):
        menubar = tk.Menu(self)
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Donations / Support", command=self._show_donate)
        help_menu.add_separator()
        help_menu.add_command(label=f"About {APP_NAME}", command=self._show_about)
        menubar.add_cascade(label="Help", menu=help_menu)
        self.config(menu=menubar)

    def _show_about(self):
        messagebox.showinfo(
            f"About {APP_NAME}",
            f"{APP_NAME} v{APP_VERSION}\n\n{APP_TAGLINE}\n\n"
            "A single-purpose desktop tool:\n"
            "  \u2022  PDF  ->  QR codes  (host + generate)\n"
            "  \u2022  Image(s)  ->  PDF\n\n"
            "Built with Python + tkinter.  Open source.")

    def _show_donate(self):
        win = tk.Toplevel(self)
        win.title(f"{APP_NAME} - Donations / Support")
        win.configure(padx=16, pady=12)
        win.resizable(False, False)
        win.transient(self)

        tk.Label(win, text="\U0001F64F  Support open-source tool development",
                 font=("TkDefaultFont", 12, "bold"), anchor="w").pack(fill="x")
        tk.Label(win, text=DONATION_TEXT, wraplength=470, justify="left",
                 anchor="w").pack(fill="x", pady=(6, 10))

        tbl = tk.Frame(win)
        tbl.pack(fill="x")
        tk.Label(tbl, text="Method", font=("TkDefaultFont", 10, "bold"),
                 anchor="w").grid(row=0, column=0, sticky="w", padx=(0, 12))
        tk.Label(tbl, text="Link", font=("TkDefaultFont", 10, "bold"),
                 anchor="w").grid(row=0, column=1, sticky="w")
        tk.Label(tbl, text="PayPal").grid(row=1, column=0, sticky="w", padx=(0, 12))
        tk.Label(tbl, text=PAYPAL_URL, fg="#0b57d0").grid(row=1, column=1, sticky="w")
        tk.Label(tbl, text="Razorpay").grid(row=2, column=0, sticky="w", padx=(0, 12))
        tk.Label(tbl, text=RAZORPAY_URL, fg="#0b57d0").grid(row=2, column=1, sticky="w")

        def copy(url):
            self.clipboard_clear()
            self.clipboard_append(url)
            flush = getattr(self, "clipboard_flush", None)
            if callable(flush):
                flush()
            self._log(f"Copied donation link: {url}")

        def open_link(url):
            try:
                webbrowser.open(url)
                self._log(f"Opening in browser: {url}")
            except Exception as e:  # noqa
                self._log(f"Could not open browser: {e}")

        btns = tk.Frame(win)
        btns.pack(pady=12, fill="x")
        tk.Button(btns, text="Copy PayPal link",
                  command=lambda: copy(PAYPAL_URL)).grid(row=0, column=0, padx=4)
        tk.Button(btns, text="Copy Razorpay link",
                  command=lambda: copy(RAZORPAY_URL)).grid(row=0, column=1, padx=4)
        tk.Button(btns, text="Open PayPal in browser",
                  command=lambda: open_link(PAYPAL_URL)).grid(row=1, column=0, padx=4, pady=(8, 0))
        tk.Button(btns, text="Open Razorpay in browser",
                  command=lambda: open_link(RAZORPAY_URL)).grid(row=1, column=1, padx=4, pady=(8, 0))

        tk.Button(win, text="Close", command=win.destroy).pack(pady=(6, 0))
        win.grab_set()
        win.focus()

    def _pick_folder(self, var):
        d = filedialog.askdirectory(title="Choose output folder")
        if d:
            var.set(d)

    # ---- logging + job plumbing ------------------------------------------ #
    def _log(self, msg):
        self.logbox.configure(state="normal")
        self.logbox.insert("end", str(msg) + "\n")
        self.logbox.see("end")
        self.logbox.configure(state="disabled")
        self.update_idletasks()

    def _poll_queue(self):
        """Pull messages posted by worker threads and update the UI."""
        try:
            while True:
                kind, payload = self._q.get_nowait()
                if kind == "log":
                    self._log(payload)
                elif kind == "qr-done":
                    self._show_qr_result(payload)
                elif kind == "pdf-done":
                    self._show_pdf_result(payload)
                elif kind == "error":
                    messagebox.showerror("fralQR", payload)
                elif kind == "done":
                    self._set_running(False)
        except queue.Empty:
            pass
        self.after(100, self._poll_queue)

    def _set_running(self, running):
        self._job_running = running
        state = "disabled" if running else "normal"
        self._set_button_states(self, state)

    def _set_button_states(self, w, state):
        if isinstance(w, tk.Button):
            with contextlib.suppress(tk.TclError):
                w.configure(state=state)
        for child in w.winfo_children():
            self._set_button_states(child, state)

    def _worker(self, func):
        """Run func (a no-arg callable that posts to self._q) in a background thread."""
        if self._job_running:
            return
        self._set_running(True)

        def run():
            try:
                func()
            except Exception as e:  # noqa
                self._q.put(("error", f"Error:\n{e}"))
            finally:
                self._q.put(("done", None))
        threading.Thread(target=run, daemon=True).start()

    # ---- job: PDF -> QR -------------------------------------------------- #
    def on_generate_qr(self):
        pdf = self.qr_file_var.get().strip()
        if not pdf or not os.path.isfile(pdf):
            messagebox.showwarning("fralQR", "Please choose a PDF file first.")
            return
        outdir = self.qr_out_var.get().strip() or os.path.dirname(pdf)
        try:
            if not os.path.isdir(outdir):
                os.makedirs(outdir, exist_ok=True)
        except OSError as e:
            messagebox.showerror("fralQR", f"Cannot create output folder:\n{e}")
            return

        self._q.put(("log", "--- PDF -> QR ---"))
        self._worker(lambda: self._run_qr_job(pdf, outdir))

    def _run_qr_job(self, pdf, outdir):
        def log(m):
            self._q.put(("log", m))
        name = os.path.splitext(os.path.basename(pdf))[0] or "menu"

        # 1) host the PDF -> public URL
        raw = host_pdf(pdf, log=log)

        # 2) build the two URLs
        viewer = build_viewer_url(raw)
        log(f"Direct URL: {raw}")
        log(f"Viewer URL: {viewer}")

        # 3) fetch the two QR PNGs
        direct_png = fetch_qr(raw)
        viewer_png = fetch_qr(viewer)

        # 4) save everything to the output folder
        d_path = os.path.join(outdir, name + "_qr_direct.png")
        v_path = os.path.join(outdir, name + "_qr_viewer.png")
        h_path = os.path.join(outdir, name + "_hosted_url.txt")
        v_url_path = os.path.join(outdir, name + "_viewer_url.txt")
        notes = os.path.join(outdir, name + "_QR_NOTES.md")
        try:
            with open(d_path, "wb") as f:
                f.write(direct_png)
            with open(v_path, "wb") as f:
                f.write(viewer_png)
            with open(h_path, "w") as f:
                f.write(raw + "\n")
            with open(v_url_path, "w") as f:
                f.write(viewer + "\n")
            with open(notes, "w") as f:
                f.write(f"# QR codes for {name}\n\n")
                f.write(f"- Hosted menu URL: {raw}\n")
                f.write(f"- Viewer URL: {viewer}\n")
                f.write("- QR files:\n")
                f.write(f"  - {os.path.basename(d_path)}  (direct link)\n")
                f.write(f"  - {os.path.basename(v_path)}  (viewer - recommended)\n")
                f.write("- Print the viewer QR: it displays the menu on any phone.\n")
        except OSError as e:
            raise RuntimeError(
                f"Could not write output files to {outdir}: {e}") from e

        log("Saved:\n  " + "\n  ".join([d_path, v_path, h_path, v_url_path, notes]))
        self._q.put(("qr-done", (d_path, v_path, raw, viewer, outdir)))

    def _show_qr_result(self, payload):
        d_path, v_path, raw, viewer, outdir = payload

        # clear any previous result content, then build fresh (no reparenting)
        for w in self.qr_result.winfo_children():
            w.destroy()

        self.qr_direct_img = tk.PhotoImage(file=d_path)
        self.qr_viewer_img = tk.PhotoImage(file=v_path)

        col1 = tk.Frame(self.qr_result)
        col1.pack(side="left", padx=20)
        tk.Label(col1, text="Direct", font=("TkDefaultFont", 9, "bold")).pack()
        tk.Label(col1, image=self.qr_direct_img, text=os.path.basename(d_path)).pack()

        col2 = tk.Frame(self.qr_result)
        col2.pack(side="left", padx=20)
        tk.Label(col2, text="Viewer (recommended)", font=("TkDefaultFont", 9, "bold")).pack()
        tk.Label(col2, image=self.qr_viewer_img, text=os.path.basename(v_path)).pack()

        for b in self.qr_urls_frame.winfo_children():
            b.destroy()
        tk.Label(self.qr_urls_frame, text="Saved to:",
                 font=("TkDefaultFont", 9, "bold")).grid(row=0, column=0, sticky="w")
        tk.Label(self.qr_urls_frame, text=outdir).grid(row=0, column=1, sticky="w")

        def copy(text):
            self.clipboard_clear()
            self.clipboard_append(text)
            flush = getattr(self, "clipboard_flush", None)
            if callable(flush):
                flush()
            self._q.put(("log", f"Copied to clipboard: {text}"))

        tk.Button(self.qr_urls_frame, text="Copy direct URL",
                  command=lambda: copy(raw)).grid(row=1, column=0, padx=4, pady=2, sticky="w")
        tk.Button(self.qr_urls_frame, text="Copy viewer URL",
                  command=lambda: copy(viewer)).grid(row=1, column=1, padx=4, pady=2, sticky="w")
        tk.Button(self.qr_urls_frame, text="Open output folder",
                  command=lambda: open_in_file_manager(outdir)).grid(
            row=2, column=0, columnspan=2, pady=2, sticky="w")

    # ---- job: Image(s) -> PDF ------------------------------------------- #
    def on_create_pdf(self):
        imgs = [x for x in self.img_var.get().split("\n") if x.strip()]
        if not imgs or not all(os.path.isfile(x) for x in imgs):
            messagebox.showwarning("fralQR", "Please choose at least one image file.")
            return
        out = self.pdf_out_var.get().strip()
        if not out:
            out = os.path.join(os.path.dirname(imgs[0]), "menu_from_images.pdf")
        if not out.lower().endswith(".pdf"):
            out += ".pdf"
        page_key = self.page_var.get()

        self._q.put(("log", "--- Image(s) -> PDF ---"))
        self._worker(lambda: self._run_pdf_job(imgs, out, page_key))

    def _run_pdf_job(self, imgs, out, page_key):
        def log(m):
            self._q.put(("log", m))
        images_to_pdf(imgs, out, page_key, log=log)
        self._q.put(("pdf-done", (out,)))

    def _show_pdf_result(self, payload):
        out, = payload
        self._log(f"Done. PDF ready at: {out}")
        if messagebox.askyesno("fralQR", f"PDF created:\n\n{out}\n\nOpen its folder?"):
            open_in_file_manager(os.path.dirname(out))


def main():
    # Pillow is only needed for the Image->PDF tab; the QR tab works without it.
    with contextlib.suppress(ImportError):
        import PIL  # noqa
    app = FralQRApp()
    app.mainloop()


if __name__ == "__main__":
    main()
