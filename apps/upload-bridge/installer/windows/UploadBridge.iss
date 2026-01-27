; Inno Setup Script for Upload Bridge
; To build: Install Inno Setup and run this script

[Setup]
AppId={{9F27C7A2-1F2D-4E3F-8C3C-D1685EDF0F5D}}
AppName=Upload Bridge
AppVersion=3.0.0
DefaultDirName={autopf}\Upload Bridge
DefaultGroupName=Upload Bridge
AllowNoIcons=yes
OutputDir=..\..\dist
OutputBaseFilename=UploadBridge_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
SetupIconFile=..\..\apps\upload-bridge\LEDMatrixStudio_icon.ico

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\..\dist\UploadBridge.exe"; DestDir: "{app}"; Flags: ignoreversion
; Include Res folder if not already bundled in EXE
; Source: "..\..\apps\upload-bridge\Res\*"; DestDir: "{app}\Res"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Upload Bridge"; Filename: "{app}\UploadBridge.exe"
Name: "{commondesktop}\Upload Bridge"; Filename: "{app}\UploadBridge.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\UploadBridge.exe"; Description: "{cm:LaunchProgram,Upload Bridge}"; Flags: nowait postinstall skipfsentry
