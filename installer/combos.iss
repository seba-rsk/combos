; Instalador de COMBOS para Windows — Inno Setup 6.
;
; Se compila con:
;   iscc installer\combos.iss
; y requiere haber construido antes dist\COMBOS\ con:
;   pyinstaller combos.spec
;
; El instalador resultante queda en dist\instalador\.
;
; Decisiones (ítem 4B del plan post-v1.1.0, ver docs/DECISIONS.md):
; instalación por usuario en %LOCALAPPDATA%\Programs\COMBOS, sin
; permisos de administrador; asociación de los archivos .combos con el
; programa (doble click abre la sesión).
;
; MyAppVersion debe mantenerse sincronizada con [project.version] del
; pyproject.toml en cada release.

#define MyAppName "COMBOS"
#define MyAppVersion "1.2.0"
#define MyAppPublisher "Sebastián A. Roskopf"
#define MyAppURL "https://github.com/seba-rsk/combos"
#define MyAppExeName "COMBOS.exe"

[Setup]
AppId={{E88F655C-CD99-4E17-ADD2-D6DFF8418D2D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}/releases
DefaultDirName={userpf}\{#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\dist\instalador
OutputBaseFilename=COMBOS_{#MyAppVersion}_instalador
SetupIconFile=..\combos.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ChangesAssociations=yes

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; \
    GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\COMBOS\*"; DestDir: "{app}"; \
    Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{userprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{userdesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; \
    Tasks: desktopicon

[Registry]
; Asociación .combos → doble click abre la sesión en COMBOS.
; En HKCU\Software\Classes porque la instalación es por usuario.
Root: HKCU; Subkey: "Software\Classes\.combos"; ValueType: string; \
    ValueName: ""; ValueData: "COMBOS.Sesion"; Flags: uninsdeletevalue
Root: HKCU; Subkey: "Software\Classes\COMBOS.Sesion"; ValueType: string; \
    ValueName: ""; ValueData: "Sesión de COMBOS"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\COMBOS.Sesion\DefaultIcon"; \
    ValueType: string; ValueName: ""; \
    ValueData: "{app}\{#MyAppExeName},0"
Root: HKCU; Subkey: "Software\Classes\COMBOS.Sesion\shell\open\command"; \
    ValueType: string; ValueName: ""; \
    ValueData: """{app}\{#MyAppExeName}"" ""%1"""

[Run]
Filename: "{app}\{#MyAppExeName}"; \
    Description: "{cm:LaunchProgram,{#MyAppName}}"; \
    Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Al desinstalar se elimina también la carpeta de datos locales (log de
; errores). Los archivos .combos del usuario viven donde él los guardó
; y no se tocan nunca.
Type: filesandordirs; Name: "{localappdata}\COMBOS"
