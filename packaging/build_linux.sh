#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Build the Linux release artifacts for fralQR:
#   - PyInstaller onedir bundle : dist/fralQR/
#   - .deb                      : dist/fralQR_<ver>_<arch>.deb
#   - .rpm                      : dist/fralQR-<ver>-<rel>.<arch>.rpm
#   - .AppImage (best effort)   : dist/fralQR-<ver>-<arch>.AppImage
#
# Run from anywhere; it cd's to the repo root itself:
#   bash packaging/build_linux.sh
#
# Needs: python3 (with venv), dpkg-deb, rpmbuild.  AppImage additionally needs
# appimagetool (the script tries to fetch it automatically).
# ---------------------------------------------------------------------------
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

VERSION="1.0.0"
APP="fralQR"
ARCH="$(dpkg --print-architecture 2>/dev/null || echo amd64)"
DIST="dist"
echo "==> fralQR ${VERSION} (${ARCH})"

# ---- build venv (pyinstaller + pillow) ----------------------------------- #
VENV="$ROOT/.build-venv"
if [ ! -x "$VENV/bin/pyinstaller" ]; then
  echo "==> creating build venv"
  python3 -m venv "$VENV"
  "$VENV/bin/pip" install --quiet --upgrade pip
  "$VENV/bin/pip" install --quiet pyinstaller pillow
fi
PYI="$VENV/bin/pyinstaller"

# ---- 1) PyInstaller onedir bundle ---------------------------------------- #
rm -rf build "$DIST/$APP"
echo "==> PyInstaller (onedir)"
"$PYI" --clean --noconfirm packaging/fralQR.spec
BUNDLE="$DIST/$APP"
[ -x "$BUNDLE/$APP" ] || { echo "bundle missing: $BUNDLE/$APP" >&2; exit 1; }

# ---- 2) .deb -------------------------------------------------------------- #
echo "==> building .deb"
STAGE="$DIST/deb-stage"
rm -rf "$STAGE"
install -d "$STAGE/DEBIAN"
install -d "$STAGE/opt/$APP"
cp -a "$BUNDLE/." "$STAGE/opt/$APP/"
install -d "$STAGE/usr/local/bin"
ln -s "/opt/$APP/$APP" "$STAGE/usr/local/bin/$APP"
install -d "$STAGE/usr/share/applications"
install -d "$STAGE/usr/share/icons/hicolor/256x256/apps"
cp packaging/fralQR.desktop "$STAGE/usr/share/applications/$APP.desktop"
cp packaging/icon.png "$STAGE/usr/share/icons/hicolor/256x256/apps/$APP.png"
INSTALLED_KB=$(du -sk "$STAGE/opt" "$STAGE/usr" 2>/dev/null | awk '{s+=$1} END{print s+0}')
[ -n "$INSTALLED_KB" ] || INSTALLED_KB=0
cat > "$STAGE/DEBIAN/control" <<EOF
Package: $APP
Version: $VERSION
Architecture: $ARCH
Maintainer: fralsare <fralsare@users.noreply.github.com>
Installed-Size: $INSTALLED_KB
Depends: libc6
Section: graphics
Priority: optional
Homepage: https://github.com/fralsare/fralQR
Description: Feed a PDF, get scannable menu QR codes (plus: build a PDF from image(s)).
 A single-purpose, cross-platform desktop app. It hosts a PDF at a public URL
 and generates two print-ready QR codes (direct and a browser "viewer"), and
 can also turn image(s) into a multi-page PDF. Uses no external browser.
EOF
chmod 0644 "$STAGE/DEBIAN/control"
rm -f "$DIST/${APP}_${VERSION}_${ARCH}.deb"
dpkg-deb --build --root-owner-group "$STAGE" "$DIST/${APP}_${VERSION}_${ARCH}.deb" >/dev/null
rm -rf "$STAGE"
echo "    -> $DIST/${APP}_${VERSION}_${ARCH}.deb"

# ---- 3) .rpm -------------------------------------------------------------- #
echo "==> building .rpm"
RB="$ROOT/.rpm"
rm -rf "$RB"; mkdir -p "$RB"/{BUILD,BUILDROOT,RPMS,SOURCES,SPECS,SRPMS}
tar czf "$RB/SOURCES/${APP}-bundle.tar.gz" -C "$DIST" "$APP"
cp packaging/rpm/$APP.spec "$RB/SPECS/"
cp packaging/fralQR.desktop "$RB/SOURCES/$APP.desktop"
cp packaging/icon.png "$RB/SOURCES/$APP.png"
rpmbuild -bb --define "_topdir $RB" "$RB/SPECS/$APP.spec"
find "$RB/RPMS" -name "*.rpm" -exec cp -f {} "$DIST/" \;
rm -rf "$RB"
echo "    -> $DIST/*.rpm"

# ---- 4) .AppImage (best effort) ------------------------------------------ #
echo "==> building .AppImage (best effort)"
AT=""
if command -v appimagetool >/dev/null 2>&1; then
  AT="appimagetool"
else
  ATBIN="$DIST/appimagetool"
  if curl -fsSL -o "$ATBIN" \
     "https://github.com/AppImage/AppImageKit/releases/download/12/appimagetool-x86_64.AppImage" \
     && [ -s "$ATBIN" ]; then
    chmod +x "$ATBIN"; AT="$ATBIN"
  fi
fi
if [ -n "$AT" ]; then
  APPDIR="$DIST/AppDir"
  rm -rf "$APPDIR"; mkdir -p "$APPDIR/usr/bin"
  cp -a "$BUNDLE/." "$APPDIR/usr/bin/"
  cp packaging/fralQR.desktop "$APPDIR/$APP.desktop"
  cp packaging/icon.png "$APPDIR/$APP.png"
  sed -i "s#^Exec=.*#Exec=$APP#" "$APPDIR/$APP.desktop"
  "$AT" "$APPDIR" "$DIST/${APP}-${VERSION}-${ARCH}.AppImage" || \
    echo "    (AppImage build failed - it is also produced by CI)"
  rm -rf "$APPDIR" "$ATBIN"
  echo "    -> $DIST/${APP}-${VERSION}-${ARCH}.AppImage"
else
  echo "    SKIPPED .AppImage (appimagetool unavailable); it is built in CI."
fi

echo "==> done. Artifacts in $DIST/:"
ls -lh "$DIST" | grep -Ev "deb-stage|AppDir" || true
