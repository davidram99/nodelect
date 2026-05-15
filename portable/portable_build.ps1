# build-portable.ps1
# Genera el empaquetado portable de Nodelect en formato .zip

$version  = "0.1"
$appName  = "nodelect"
$zipName  = "$appName-portable-$version.zip"
$tempDir  = "$PSScriptRoot\$appName-portable"
$root     = Split-Path $PSScriptRoot -Parent

Write-Host "Generando portable $zipName..."

# Limpiar temp si ya existe
if (Test-Path $tempDir) {
    Remove-Item -Recurse -Force $tempDir
}

# Crear estructura de carpetas
New-Item -ItemType Directory -Force -Path "$tempDir"        | Out-Null
New-Item -ItemType Directory -Force -Path "$tempDir\shims"  | Out-Null

function Copy-PreferredShim {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Root,
        [Parameter(Mandatory = $true)]
        [string]$Name,
        [Parameter(Mandatory = $true)]
        [string]$Destination
    )

    $exePath = "$Root\dist\shims\$Name.exe"
    $cmdPath = "$Root\dist\shims\$Name.cmd"

    if (Test-Path $exePath) {
        Copy-Item $exePath $Destination
        return
    }

    if (Test-Path $cmdPath) {
        Copy-Item $cmdPath $Destination
        return
    }

    throw "No se encontró shim para '$Name' (.exe o .cmd) en dist\shims"
}

# Copiar archivos
Copy-Item "$root\dist\nodelect.exe"       "$tempDir\"
Copy-PreferredShim -Root $root -Name "node" -Destination "$tempDir\shims\"
Copy-PreferredShim -Root $root -Name "npm"  -Destination "$tempDir\shims\"
Copy-PreferredShim -Root $root -Name "npx"  -Destination "$tempDir\shims\"
Copy-Item "$root\assets\icon.ico"         "$tempDir\"

# Generar ZIP (sobreescribe si ya existe)
$zipPath = "$PSScriptRoot\$zipName"
if (Test-Path $zipPath) {
    Remove-Item -Force $zipPath
}
Compress-Archive -Path "$tempDir\*" -DestinationPath $zipPath

# Limpiar carpeta temporal
Remove-Item -Recurse -Force $tempDir

Write-Host "Listo: $zipPath"