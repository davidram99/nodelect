# nodelect — Guía de Compilación en Windows

Instrucciones completas para compilar `nodelect` en Windows usando **Nuitka** y **GCC (MinGW-w64)**, partiendo desde un sistema limpio.

> **Versión objetivo:** Python 3.13 · Nuitka ≥ 4.0.5 · Windows x86_64

---

## Índice

1. [Deshacer una instalación previa](#1-deshacer-una-instalación-previa)
2. [Requisitos previos](#2-requisitos-previos)
3. [Compilación paso a paso](#3-compilación-paso-a-paso)
4. [Verificación del resultado](#4-verificación-del-resultado)
5. [Solución de problemas](#5-solución-de-problemas)
6. [Resumen rápido](#6-resumen-rápido)

---

## 1. Deshacer una instalación previa

Si ya seguiste una versión anterior de esta guía, limpia el entorno antes de empezar de nuevo.

### 1.1 Eliminar MSYS2 y MinGW-w64

```powershell
# Desinstalar MSYS2 vía winget
winget uninstall --id MSYS2.MSYS2

# Eliminar el directorio residual (ajusta si instalaste en otra ruta)
Remove-Item -Recurse -Force "C:\msys64"
```

Si instalaste MinGW-w64 de forma manual (sin MSYS2), elimina también su carpeta raíz:

```powershell
Remove-Item -Recurse -Force "C:\mingw64"   # ajusta según tu ruta
```

### 1.2 Limpiar el PATH del sistema

1. Abre **Inicio → Editar las variables de entorno del sistema → Variables de entorno**.
2. En **Variables del sistema**, selecciona `Path` y haz clic en **Editar**.
3. Elimina cualquier entrada que contenga `mingw64\bin` o `msys64`.
4. Acepta y cierra.

Verifica que GCC ya no está disponible:

```powershell
gcc --version
# Debe responder: "gcc : El término 'gcc' no se reconoce..."
```

### 1.3 Eliminar el entorno virtual de uv y artefactos de compilación

```powershell
# Desde la raíz del proyecto
Remove-Item -Recurse -Force .venv
Remove-Item -Recurse -Force dist
Remove-Item -Recurse -Force *.build   # carpetas temporales de Nuitka
```

### 1.4 Limpiar la caché de Nuitka

Nuitka almacena su runtime de C descargado en una carpeta de usuario:

```powershell
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\Nuitka"
```

---

## 2. Requisitos previos

### 2.1 uv

Instala `uv` si aún no lo tienes. Es el gestor de entornos y dependencias del proyecto:

```powershell
winget install --id astral-sh.uv
```

Verifica la instalación (cierra y reabre la terminal primero):

```powershell
uv --version
```

### 2.2 GCC — MinGW-w64 vía MSYS2

Nuitka descarga su propio GCC automáticamente durante la primera compilación, pero para compilar los **shims** en C necesitas tener GCC disponible en el PATH del sistema.

#### Instalación

```powershell
winget install -e --id MSYS2.MSYS2
```

Cuando termine, **abre la terminal de MSYS2** (no PowerShell) y ejecuta:

```bash
pacman -Syu
pacman -S --needed base-devel mingw-w64-x86_64-toolchain
```

#### Agregar GCC al PATH de Windows

1. Abre **Inicio → Editar las variables de entorno del sistema → Variables de entorno**.
2. En **Variables del sistema**, selecciona `Path` → **Editar → Nuevo**.
3. Añade la ruta:
   ```
   C:\msys64\mingw64\bin
   ```
4. Acepta y cierra.

#### Verificación

Abre una nueva terminal PowerShell y comprueba:

```powershell
gcc --version
# Ejemplo de salida esperada:
# gcc (Rev1, Built by MSYS2 project) 13.x.x
```

> **Alternativa sin MSYS2:** Descarga un paquete portable desde [winlibs.com](https://winlibs.com/) — elige la variante `x86_64 / POSIX / UCRT`. Extrae el contenido y añade su carpeta `bin` al PATH del mismo modo.

### 2.3 Configurar el entorno del proyecto

Desde la raíz del proyecto, crea el entorno virtual e instala todas las dependencias (incluye Nuitka ≥ 4.0.5 y zstandard ≥ 0.25.0 tal y como están declaradas en `pyproject.toml`):

```powershell
uv sync
```

Verifica que Nuitka y zstandard están disponibles:

```powershell
uv run python -m nuitka --version
uv run python -c "import zstandard; print(zstandard.__version__)"
```

---

## 3. Compilación paso a paso

> **Importante:** La documentación oficial de Nuitka recomienda probar primero con `--mode=standalone` antes de pasar a `--mode=onefile`. Los problemas de archivos de datos son mucho más fáciles de diagnosticar en modo standalone.

### 3.1 Shims

Los shims son tres ejecutables C pequeños (`node.exe`, `npm.exe`, `npx.exe`) que se generan con GCC. El script `shims/build.bat` crea el directorio `dist\shims` si no existe y compila los tres desde `shims/shim.c`:

```powershell
.\shims\build.bat
```

Salida esperada:

```
Shims generados en ..\dist\shims
```

Verifica que los tres archivos se crearon:

```powershell
dir dist\shims
# Debe listar node.exe, npm.exe y npx.exe
```

### 3.2 Ejecutable principal — modo standalone (diagnóstico)

Compila primero en modo standalone para detectar problemas de dependencias antes de empaquetar en un solo archivo:

```powershell
uv run python -m nuitka `
  --mode=standalone `
  --windows-icon-from-ico=assets/icon.ico `
  --output-dir=dist `
  --output-filename=nodelect.exe `
  src/nodelect/cli.py
```

El resultado quedará en `dist\cli.dist\`. Prueba el ejecutable desde ahí antes de continuar:

```powershell
dist\cli.dist\nodelect.exe --help
```

### 3.3 Ejecutable principal — modo onefile (distribución)

Si el paso anterior funcionó sin errores, genera el binario final de un solo archivo:

```powershell
uv run python -m nuitka `
  --mode=onefile `
  --windows-icon-from-ico=assets/icon.ico `
  --output-dir=dist `
  --output-filename=nodelect.exe `
  src/nodelect/cli.py
```

> **Nota sobre flags:**
> - `--mode=onefile` incluye automáticamente el comportamiento de `--mode=standalone`. **No es necesario especificar ambos** — hacerlo con la sintaxis antigua `--standalone --onefile` genera un warning en versiones recientes de Nuitka.
> - El backtick `` ` `` es el carácter de continuación de línea en PowerShell. Si usas **CMD**, sustitúyelo por `^`.

El binario final quedará en:

```
dist\nodelect.exe
```

La primera ejecución tardará varios minutos porque Nuitka descarga y compila su propio runtime de C. Las compilaciones posteriores son más rápidas gracias a la caché interna (ccache).

---

## 4. Verificación del resultado

```powershell
# Comprobar que el ejecutable existe y tiene un tamaño razonable
dir dist\nodelect.exe

# Ejecutar el binario compilado
dist\nodelect.exe --help
```

Para verificar que funciona en una máquina limpia (sin Python instalado), copia únicamente `dist\nodelect.exe` a otro equipo o a una VM sin Python y ejecútalo.

---

## 5. Solución de problemas

| Síntoma | Causa probable | Solución |
|---|---|---|
| `gcc: command not found` | GCC no está en el PATH | Añade `C:\msys64\mingw64\bin` al PATH y abre una nueva terminal |
| `ModuleNotFoundError: zstandard` | Dependencia no instalada | Ejecuta `uv sync` |
| Warning sobre `--standalone` y `--onefile` combinados | Flags redundantes en Nuitka moderno | Usa únicamente `--mode=onefile` |
| Error al descargar el C runtime de Nuitka | Sin conexión a internet | Asegúrate de tener conexión en la primera compilación |
| Antivirus bloquea el recurso del `.exe` | Windows Defender interfiere con el post-procesado | Desactiva temporalmente la protección en tiempo real durante la compilación o añade la carpeta del proyecto a las exclusiones |
| El `.exe` no arranca en otra máquina | Python no incluido correctamente | Verifica primero con `--mode=standalone`; si falla, busca módulos ausentes en la salida de Nuitka |
| `shims\build.bat` falla con "acceso denegado" | El directorio `dist\shims` ya existe y está bloqueado | Elimina `dist\shims` manualmente y vuelve a ejecutar |

---

## 6. Resumen rápido

```powershell
# 1. Instalar MSYS2 + GCC (solo la primera vez)
winget install -e --id MSYS2.MSYS2
# (abre MSYS2 y ejecuta: pacman -S --needed base-devel mingw-w64-x86_64-toolchain)
# Añade C:\msys64\mingw64\bin al PATH del sistema

# 2. Configurar el entorno del proyecto
uv sync

# 3. Verificar dependencias
gcc --version
uv run python -m nuitka --version
uv run python -c "import zstandard; print(zstandard.__version__)"

# 4. Compilar los shims
.\shims\build.bat

# 5. Compilar el ejecutable (onefile)
uv run python -m nuitka `
  --mode=onefile `
  --windows-icon-from-ico=assets/icon.ico `
  --output-dir=dist `
  --output-filename=nodelect.exe `
  src/nodelect/cli.py
```