# Changelog

All notable changes to **fralQR** are documented in this file.

This project adheres to [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and uses [Semantic Versioning](https://semver.org/).

## [1.0.0] - 2026

### Added
- Initial public release.
- **PDF → QR codes**: host a PDF on Catbox.moe and generate a *direct* and a
  *viewer* QR code (600×600, high error-correction), saved alongside their URLs
  and a notes file.
- **Image(s) → PDF**: build a multi-page A4/Letter PDF from one or more images (Pillow).
- Cross-platform tkinter GUI for Windows and Linux (own window, no browser).
- Automatic retries on transient network errors (HTTP 5xx / 429) from the QR service.
- In-app **Donations / Support** dialog and **About**.
- Release packaging: `.AppImage`, `.deb`, `.rpm` (Linux) and installer `.exe`
  plus portable `.exe` (Windows), built automatically via GitHub Actions.

### Fixed
- **Windows build (CI + script)**: fixed a `cmd.exe` parse error
  (`… was unexpected at this time`) caused by parentheses inside `echo` text
  within multi-line `if (…)` blocks in `packaging/build_windows.bat` and
  `fralQR.bat`. Inno Setup's `ISCC.exe` is now located reliably (PATH, then the
  standard install dirs) so the installer step no longer depends on Chocolatey
  having added it to the current shell's `PATH`.
