[Setup]
AppName=Nodelect
AppVersion=0.1
AppId={{D4DE5911-8CD4-49E3-9216-D93541B60732}
AppPublisher=Develoz
AppPublisherURL=https://github.com/davidram99
SetupIconFile=..\assets\icon.ico
DefaultDirName={localappdata}\nodelect
PrivilegesRequired=lowest
DisableProgramGroupPage=yes
OutputDir=..\installer\output
OutputBaseFilename=nodelect-setup-0.1
WizardStyle=modern
Compression=lzma2
SolidCompression=yes

[Files]
Source: "..\dist\nodelect.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\shims\node.exe"; DestDir: "{app}\shims"; Flags: ignoreversion
Source: "..\dist\shims\npm.exe"; DestDir: "{app}\shims"; Flags: ignoreversion
Source: "..\dist\shims\npx.exe"; DestDir: "{app}\shims"; Flags: ignoreversion
Source: "..\assets\icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\Nodelect"; Filename: "{app}\nodelect.exe"; IconFilename: "{app}\icon.ico"

[Code]
const
  WM_SETTINGCHANGE = $001A;
  SMTO_ABORTIFHUNG = $0002;

function SendMessageTimeout(hWnd: Integer; Msg: Integer; wParam: Integer; lParam: string;
  fuFlags: Integer; uTimeout: Integer; out lpdwResult: Integer): Integer;
  external 'SendMessageTimeoutW@user32.dll stdcall';

// NOTA: NormalizePath usa LowerCase, que solo es fiable con caracteres ASCII.
// Rutas del PATH del usuario que contengan caracteres Unicode (á, é, ñ, ü, etc.)
// podrían no compararse correctamente, causando entradas duplicadas al instalar
// o entradas no eliminadas al desinstalar. En la práctica el riesgo es bajo ya
// que {localappdata}\nodelect no contiene dichos caracteres, pero un futuro
// mantenedor debería resolverlo usando CompareString de la WinAPI con
// NORM_IGNORECASE si se necesita robustez total.
function NormalizePath(const S: string): string;
begin
  Result := Trim(S);
  while (Length(Result) > 0) and (Copy(Result, Length(Result), 1) = '\') do
    Delete(Result, Length(Result), 1);
  Result := LowerCase(Result);
end;

function PathEquals(const A, B: string): Boolean;
begin
  Result := NormalizePath(A) = NormalizePath(B);
end;

function JoinPathTokens(const Tokens: TArrayOfString): string;
var
  I: Integer;
begin
  Result := '';
  for I := 0 to GetArrayLength(Tokens) - 1 do
  begin
    if Tokens[I] = '' then
      continue;

    if Result = '' then
      Result := Tokens[I]
    else
      Result := Result + ';' + Tokens[I];
  end;
end;

function SplitPathTokens(const PathValue: string): TArrayOfString;
var
  Work: string;
  SepPos: Integer;
  Token: string;
begin
  SetArrayLength(Result, 0);
  Work := PathValue;

  while True do
  begin
    SepPos := Pos(';', Work);
    if SepPos = 0 then
    begin
      Token := Trim(Work);
      if Token <> '' then
      begin
        SetArrayLength(Result, GetArrayLength(Result) + 1);
        Result[GetArrayLength(Result) - 1] := Token;
      end;
      break;
    end;

    Token := Trim(Copy(Work, 1, SepPos - 1));
    if Token <> '' then
    begin
      SetArrayLength(Result, GetArrayLength(Result) + 1);
      Result[GetArrayLength(Result) - 1] := Token;
    end;

    Delete(Work, 1, SepPos);
  end;
end;

function PathContains(const PathValue, Param: string): Boolean;
var
  Tokens: TArrayOfString;
  I: Integer;
begin
  Result := False;
  Tokens := SplitPathTokens(PathValue);
  for I := 0 to GetArrayLength(Tokens) - 1 do
  begin
    if PathEquals(Tokens[I], Param) then
    begin
      Result := True;
      exit;
    end;
  end;
end;

procedure AddToUserPath(const Param: string);
var
  OrigPath, NewPath: string;
begin
  if not RegQueryStringValue(HKCU, 'Environment', 'Path', OrigPath) then
    OrigPath := '';

  if PathContains(OrigPath, Param) then
    exit;

  if OrigPath = '' then
    NewPath := Param
  else
    NewPath := OrigPath + ';' + Param;

  RegWriteExpandStringValue(HKCU, 'Environment', 'Path', NewPath);
end;

procedure RemoveFromUserPath(const Param: string);
var
  OrigPath, NewPath: string;
  Tokens, Kept: TArrayOfString;
  I, CountKept: Integer;
begin
  if not RegQueryStringValue(HKCU, 'Environment', 'Path', OrigPath) then
    exit;

  Tokens := SplitPathTokens(OrigPath);
  SetArrayLength(Kept, GetArrayLength(Tokens));
  CountKept := 0;

  for I := 0 to GetArrayLength(Tokens) - 1 do
  begin
    if not PathEquals(Tokens[I], Param) then
    begin
      Kept[CountKept] := Tokens[I];
      CountKept := CountKept + 1;
    end;
  end;

  SetArrayLength(Kept, CountKept);
  NewPath := JoinPathTokens(Kept);

  if NewPath <> OrigPath then
  begin
    if NewPath = '' then
      RegDeleteValue(HKCU, 'Environment', 'Path')
    else
      RegWriteExpandStringValue(HKCU, 'Environment', 'Path', NewPath);
  end;
end;

procedure RefreshEnvironment;
var
  ResultCode: Integer;
begin
  SendMessageTimeout($FFFF, WM_SETTINGCHANGE, 0, 'Environment',
    SMTO_ABORTIFHUNG, 5000, ResultCode);
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    AddToUserPath(ExpandConstant('{localappdata}\nodelect\shims'));
    AddToUserPath(ExpandConstant('{localappdata}\nodelect'));
    RefreshEnvironment;
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
  begin
    RemoveFromUserPath(ExpandConstant('{localappdata}\nodelect\shims'));
    RemoveFromUserPath(ExpandConstant('{localappdata}\nodelect'));
    RefreshEnvironment;

    if MsgBox(
      '¿Desea eliminar también las versiones de Node instaladas y todos sus componentes?',
      mbConfirmation, MB_YESNO) = IDYES then
      DelTree(ExpandConstant('{app}'), True, True, True);
  end;
end;
