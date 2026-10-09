; ---------------------------------------------------------------------------
; fralQR - Windows installer script (Inno Setup 6)
;
; Build the PyInstaller onedir folder first (packaging/build_windows.bat does
; this), then compile this script:
;   iscc packaging/fralQR.iss
;
; Output: dist/fralQR-Setup-<version>.exe
; ---------------------------------------------------------------------------

#define MyAppName "fralQR"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "fralsare"
#define MyAppURL "https://github.com/fralsare/fralQR"
#define MyAppExeName "fralQR.exe"

[Setup]
; NOTE: AppId must stay the same across versions so upgrades work.
AppId={{6E2A7C41-9B3D-4F1E-8A2C-5D4E0B9F2C17}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\fralQR
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
Output=..\dist
OutputBaseFilename=fralQR-Setup-{#MyAppVersion}
SetupIconFile=icon.ico
UninstallDisplayIcon={app}\fralQR.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
; 64-bit installers only (the bundle is built for x64)
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\fralQR\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\fralQR"; Filename: "{app}\fralQR.exe"
Name: "{group}\Uninstall fralQR"; Filename: "{uninstallexe}"
Name: "{autodesktop}\fralQR"; Filename: "{app}\fralQR.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
