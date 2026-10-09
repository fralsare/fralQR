Name:           fralQR
Version:        1.0.0
Release:        1%{?dist}
Summary:        Feed a PDF, get scannable menu QR codes (plus: build a PDF from image(s))
License:        MIT
URL:            https://github.com/fralsare/fralQR

%description
fralQR is a single-purpose, cross-platform desktop app. It hosts a PDF at a
public URL and generates two print-ready QR codes (a "direct" link and a
browser "viewer"), and can also turn image(s) into a multi-page PDF. It opens
in its own window and uses no external browser. The app is fully bundled (its
own Python runtime is included), so no system Python packages are required.

%prep
# The PyInstaller onedir bundle is provided prebuilt in SOURCES as a tarball.
# Nothing to unpack into the build tree.

%build
# Nothing to compile - the app is bundled by PyInstaller upstream.

%install
rm -rf %{buildroot}
install -d %{buildroot}/opt/%{name}
tar xzf %{_sourcedir}/%{name}-bundle.tar.gz -C %{buildroot}/opt/%{name} \
  --strip-components=1
install -d %{buildroot}/usr/local/bin
ln -s /opt/%{name}/%{name} %{buildroot}/usr/local/bin/%{name}
install -d %{buildroot}/usr/share/applications
cp %{_sourcedir}/%{name}.desktop %{buildroot}/usr/share/applications/
install -d %{buildroot}/usr/share/icons/hicolor/256x256/apps
cp %{_sourcedir}/%{name}.png \
  %{buildroot}/usr/share/icons/hicolor/256x256/apps/%{name}.png
chmod 0755 %{buildroot}/opt/%{name}/%{name}
# RPM %files globs do not recurse and %files -f needs absolute paths, so
# build a recursive manifest (each path prefixed with "/") and feed it in.
( cd %{buildroot} \
  && { find opt/%{name} -print | sed 's#^#/#' | sort
       echo /usr/local/bin/%{name}
       echo /usr/share/applications/%{name}.desktop
       echo /usr/share/icons/hicolor/256x256/apps/%{name}.png ; } \
  > %{_topdir}/%{name}.fileslist )

%files -f %{_topdir}/%{name}.fileslist

%changelog
* Tue Feb 03 2026 fralsare <fralsare@users.noreply.github.com> - 1.0.0-1
- Initial release.
