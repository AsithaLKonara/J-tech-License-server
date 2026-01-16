; Upload Bridge – Inno Setup installer (PySide6 + PyInstaller, offline licensing)

#define AppName "Upload Bridge"
#define AppVersion "3.0.0"
#define Publisher "LED Matrix Studio"
#define Website "https://example.com"
#define AppExe "UploadBridge.exe"
#define LauncherVBS "LAUNCH_UPLOAD_BRIDGE.vbs"
#define LauncherBAT "LAUNCH_UPLOAD_BRIDGE.bat"
#define DebugBAT "LAUNCH_UPLOAD_BRIDGE_DEBUG.bat"

; INPUT PATHS (adjust for your repo layout)
#define DistDir "..\\dist"
#define ExePath DistDir + "\\UploadBridge.exe"
#define VbsPath "..\\windows\\" + LauncherVBS
#define BatPath "..\\windows\\" + LauncherBAT
#define DebugPath "..\\windows\\" + DebugBAT
#define KeysPath "..\\LICENSE_KEYS.txt"
#define IconPath "..\\LEDMatrixStudio_icon.ico"
#define EULAPath "EULA.txt"

[Setup]
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#Publisher}
AppPublisherURL={#Website}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableDirPage=no
DisableProgramGroupPage=no
OutputDir=dist
OutputBaseFilename=UploadBridge_Setup_{#AppVersion}
SetupIconFile={#IconPath}
LicenseFile={#EULAPath}
WizardStyle=modern
Compression=lzma2
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=admin
UninstallDisplayIcon={app}\{#AppExe}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"; LicenseFile: "{#EULAPath}"

[Files]
; Main EXE (onefile)
Source: "{#ExePath}"; DestDir: "{app}"; Flags: ignoreversion;
; Launchers
Source: "{#VbsPath}"; DestDir: "{app}"; Flags: ignoreversion;
Source: "{#BatPath}"; DestDir: "{app}"; Flags: ignoreversion;
Source: "{#DebugPath}"; DestDir: "{app}"; Flags: ignoreversion;
; License keys for offline activation
Source: "{#KeysPath}"; DestDir: "{app}"; Flags: ignoreversion;

[Icons]
Name: "{commondesktop}\{#AppName}"; Filename: "{app}\{#LauncherVBS}"; WorkingDir: "{app}"; IconFilename: "{app}\{#AppExe}";
Name: "{group}\{#AppName}"; Filename: "{app}\{#LauncherVBS}"; WorkingDir: "{app}"; IconFilename: "{app}\{#AppExe}";
Name: "{group}\{#AppName} (Debug)"; Filename: "{app}\{#DebugBAT}"; WorkingDir: "{app}";
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}";

[Run]
Filename: "{app}\{#LauncherVBS}"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent; WorkingDir: "{app}"

[Registry]
; --- File Associations (.bin / .dat / .leds) ---
; Associates Upload Bridge with firmware and LED data files (uses VBS launcher to hide console)

Root: HKCR; Subkey: ".bin";  ValueType: string; ValueData: "UploadBridge.binfile";  Flags: uninsdeletevalue
Root: HKCR; Subkey: "UploadBridge.binfile"; ValueType: string; ValueData: "BIN File for Upload Bridge"; Flags: uninsdeletekey
Root: HKCR; Subkey: "UploadBridge.binfile\DefaultIcon"; ValueType: string; ValueData: "{app}\{#AppExe},0"
Root: HKCR; Subkey: "UploadBridge.binfile\shell\open\command"; ValueType: string; ValueData: """{app}\{#LauncherVBS}"" """%1"""

Root: HKCR; Subkey: ".dat";  ValueType: string; ValueData: "UploadBridge.datfile";  Flags: uninsdeletevalue
Root: HKCR; Subkey: "UploadBridge.datfile"; ValueType: string; ValueData: "DAT File for Upload Bridge"; Flags: uninsdeletekey
Root: HKCR; Subkey: "UploadBridge.datfile\DefaultIcon"; ValueType: string; ValueData: "{app}\{#AppExe},0"
Root: HKCR; Subkey: "UploadBridge.datfile\shell\open\command"; ValueType: string; ValueData: """{app}\{#LauncherVBS}"" """%1"""

Root: HKCR; Subkey: ".leds"; ValueType: string; ValueData: "UploadBridge.ledsfile"; Flags: uninsdeletevalue
Root: HKCR; Subkey: "UploadBridge.ledsfile"; ValueType: string; ValueData: "LEDS File for Upload Bridge"; Flags: uninsdeletekey
Root: HKCR; Subkey: "UploadBridge.ledsfile\DefaultIcon"; ValueType: string; ValueData: "{app}\{#AppExe},0"
Root: HKCR; Subkey: "UploadBridge.ledsfile\shell\open\command"; ValueType: string; ValueData: """{app}\{#LauncherVBS}"" """%1"""

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
end;


