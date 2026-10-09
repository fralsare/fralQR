# Publishing fralQR to GitHub (step by step)

This walks you through pushing the source to your GitHub account and cutting a
release that ships all five binaries. Everything is copy-paste.

> Your account: **fralsare** → repo will be `github.com/fralsare/fralQR`.
> Your GitHub email used here: `fralsare@users.noreply.github.com` (GitHub's
> default private email — you can change it with the `user.email` step below).

---

## 0) One-time prep

Install `git` if you don't have it:

```bash
sudo apt install git        # Debian/Ubuntu
```

Set your identity (only needed once):

```bash
git config --global user.name  "fralsare"
git config --global user.email "fralsare@users.noreply.github.com"
```

Make sure GitHub access works. Either:
- use a **Personal Access Token** (Settings → Developer settings → Tokens →
  "Generate new token (classic)", scope `repo`), or
- use **SSH** (`ssh-keygen` then add the public key to GitHub).

The commands below assume a token via HTTPS. Replace `YOURTOKEN` with your token
when prompted, or add it to your keyring first:

```bash
git config --global credential.helper store
```

---

## 1) Create the empty repo on GitHub

1. Go to <https://github.com/new>.
2. **Repository name:** `fralQR`
3. **Description:** `Feed a PDF, get scannable menu QR codes — in its own window.`
4. **Public** (open source).
5. Do **not** check "Add a README", ".gitignore", or license — the repo already
   has all of those. Click **Create repository**.

---

## 2) Init, commit, and push the source

Run all of this **from inside the `fralQR` folder** (the one containing
`fralQR.py`, `README.md`, etc.):

```bash
cd /run/media/fralsare/WD240gb/ResturantQRCodeProject/Menu/fralQR

git init -b main
git add -A

# SANITY CHECK: this must NOT list AppTest/, dist/, build/, pdf/, images/, Out/
git status --short

git commit -m "fralQR v1.0.0: single-purpose PDF -> QR menu app (Linux + Windows)"

git remote add origin https://github.com/fralsare/fralQR.git
git push -u origin main
```

> If `git status --short` shows anything under `AppTest/`, `dist/`, or your data
> folders, the `.gitignore` wasn't applied — stop and tell me. Those folders must
> stay out of the repo.

---

## 3) Enable the release build

The workflow in `.github/workflows/build.yml` builds all five artifacts
(`.deb`, `.rpm`, `.AppImage`, Windows installer `.exe`, Windows portable `.exe`)
**on every tag** matching `v*.*.*`. It does this automatically — no extra
setup needed.

---

## 4) Create the release (lets CI build the binaries)

From the `fralQR` folder:

```bash
cd /run/media/fralsare/WD240gb/ResturantQRCodeProject/Menu/fralQR

# 4a) tag + push the tag (this TRIGGERS the CI build)
git tag -a v1.0.0 -m "fralQR v1.0.0"
git push origin v1.0.0
```

Then go to the repo and **finish** the release that GitHub auto-created:

1. Open <https://github.com/fralsare/fralQR/releases> — you'll see a
   **`v1.0.0`** (draft) entry.
2. Click **Edit**.
3. Paste a short note, e.g.:
   ```
   fralQR v1.0.0
   - Feed a PDF, get two print-ready menu QR codes (viewer + direct)
   - Image(s) -> PDF
   - In-app donations (Help > Donations)
   ```
4. Make sure **"Attach assets"** is on.
5. Wait for CI: <https://github.com/fralsare/fralQR/actions>. The
   **"Build & attach release artifacts"** job runs the Linux + Windows builds,
   then uploads all five files as release assets.
6. Click **Publish release**.

> The builds take a few minutes (Python + PyInstaller install + compile).
> When the job is green, the five files appear under the release.

---

## 5) (Alternative) Upload the binaries you built locally

You already have the **Linux** artifacts built in `dist/`:

```
dist/fralQR_1.0.0_amd64.deb
dist/fralQR-1.0.0-1.x86_64.rpm
dist/fralQR-1.0.0-amd64.AppImage
```

Option A — **web UI**: on the release page, drag the files from `dist/` into the
"Attach binaries" box (Windows `.exe` files if you built them on a Windows box).

Option B — **`gh` CLI** (fastest; `brew install gh` / `apt install gh`, then
`gh auth login`):

```bash
cd /run/media/fralsare/WD240gb/ResturantQRCodeProject/Menu/fralQR

# create the release if it doesn't exist, then attach the local files
gh release create v1.0.0 \
  --title "fralQR v1.0.0" \
  --notes "Feed a PDF, get scannable menu QR codes." \
  --target main \
  "dist/fralQR_1.0.0_amd64.deb" \
  "dist/fralQR-1.0.0-1.x86_64.rpm" \
  "dist/fralQR-1.0.0-amd64.AppImage"
```

Add the Windows files the same way (they're not built on Linux; get them from CI
or a Windows machine via `packaging\build_windows.bat`), e.g.:

```bash
gh release upload v1.0.0 "fralQR-Setup-1.0.0.exe" "fralQR-1.0.0-portable.exe"
```

---

## 6) Verify

- <https://github.com/fralsare/fralQR> — README renders, badges show, folder list
  does **not** include `AppTest/`.
- <https://github.com/fralsare/fralQR/releases/tag/v1.0.0> — five assets present.
- Download one and run it (e.g. `chmod +x fralQR-*.AppImage && ./fralQR-*.AppImage`).

---

## Releasing a new version later

```bash
# bump APP_VERSION in fralQR.py (e.g. 1.1.0), note the change in CHANGELOG.md
git commit -am "v1.1.0: <what changed>"
git tag -a v1.1.0 -m "fralQR v1.1.0"
git push origin main v1.1.0     # CI rebuilds + the release attaches the new binaries
# then finish the release on /releases as in step 4
```

That's it — tag, push, and the binaries build themselves.
