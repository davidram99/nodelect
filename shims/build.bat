@echo off
cd %~dp0
set OUT=..\dist\shims
if not exist %OUT% mkdir %OUT%

gcc -O2 -o %OUT%\node.exe shim.c -lkernel32
gcc -O2 -o %OUT%\npm.exe  shim.c -lkernel32
gcc -O2 -o %OUT%\npx.exe  shim.c -lkernel32

echo Shims generados en %OUT%