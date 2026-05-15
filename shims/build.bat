@echo off
cd %~dp0
set OUT=..\dist\shims
if not exist %OUT% mkdir %OUT%

if "%~1"=="--secure-shim" goto build_cmd

gcc -O2 -o %OUT%\node.exe shim.c -lkernel32
gcc -O2 -o %OUT%\npm.exe  shim.c -lkernel32
gcc -O2 -o %OUT%\npx.exe  shim.c -lkernel32

echo Shims .exe generados en %OUT%
goto :eof

:build_cmd
gcc -O2 -o %OUT%\cmd_shim_gen.exe cmd_shim.c
if errorlevel 1 goto :eof

%OUT%\cmd_shim_gen.exe %OUT%
del /q %OUT%\cmd_shim_gen.exe >nul 2>nul

echo Shims .cmd generados en %OUT%
goto :eof