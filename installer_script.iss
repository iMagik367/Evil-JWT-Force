[Setup]
AppName=EVIL_JWT_FORCE
AppVersion=1.0.0
DefaultDirName={pf}\EVIL_JWT_FORCE
DisableDirPage=no
DefaultGroupName=EVIL_JWT_FORCE
OutputDir=.
OutputBaseFilename=EVIL_JWT_FORCE_Installer
Compression=lzma
SolidCompression=yes

[Files]
// ... existing code ...
Source: "external\theHarvester\*"; DestDir: "{app}\external\theHarvester"; Flags: recursesubdirs createallsubdirs
Source: "dist\main.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "requirements.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "install_deps.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "gui\assets\*"; DestDir: "{app}\gui\assets"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "config\*"; DestDir: "{app}\config"; Flags: recursesubdirs createallsubdirs
Source: "output\*"; DestDir: "{app}\output"; Flags: recursesubdirs createallsubdirs
Source: "logs\*"; DestDir: "{app}\logs"; Flags: recursesubdirs createallsubdirs
Source: "reports\*"; DestDir: "{app}\reports"; Flags: recursesubdirs createallsubdirs
Source: "core\*"; DestDir: "{app}\core"; Flags: recursesubdirs createallsubdirs
Source: "modules\*"; DestDir: "{app}\modules"; Flags: recursesubdirs createallsubdirs
Source: "utils\*"; DestDir: "{app}\utils"; Flags: recursesubdirs createallsubdirs
Source: "scripts\*"; DestDir: "{app}\scripts"; Flags: recursesubdirs createallsubdirs
Source: "gui\*"; DestDir: "{app}\gui"; Flags: recursesubdirs createallsubdirs
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion
// ... existing code ...

[Icons]
Name: "{group}\EVIL_JWT_FORCE"; Filename: "{app}\main.exe"

[Run]
Filename: "{cmd}"; Parameters: "/C python {app}\install_deps.py"; Description: "Instalar dependências Python"; Flags: runhidden
// ... existing code ...