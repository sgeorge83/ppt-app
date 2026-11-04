# Build the Store payload and, when the Windows SDK is present, the MSIX.
# Run from the repository root:
#   powershell -ExecutionPolicy Bypass -File packaging\build_msix.ps1

param(
    [string]$Version = "1.0.2.0"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

python packaging\prepare_data.py
python packaging\fetch_font.py
python packaging\generate_assets.py
python -m pip install -r requirements.txt
python -m PyInstaller --noconfirm --clean wordonair-slides.spec

$Payload = Join-Path $Root "dist\WordOnAirSlides"
if (-not (Test-Path (Join-Path $Payload "WordOnAirSlides.exe"))) {
    throw "PyInstaller output missing: $Payload\WordOnAirSlides.exe"
}

Copy-Item (Join-Path $Root "packaging\AppxManifest.xml") (Join-Path $Payload "AppxManifest.xml") -Force
$Assets = Join-Path $Payload "Assets"
New-Item -ItemType Directory -Force -Path $Assets | Out-Null
Copy-Item (Join-Path $Root "packaging\Assets\*") $Assets -Force

$Fonts = Join-Path $Payload "Fonts"
New-Item -ItemType Directory -Force -Path $Fonts | Out-Null
Copy-Item (Join-Path $Root "packaging\Fonts\*") $Fonts -Force

$dataDest = Join-Path $Payload "data"
New-Item -ItemType Directory -Force -Path $dataDest | Out-Null
Copy-Item (Join-Path $Root "data\english") (Join-Path $dataDest "english") -Recurse -Force
Copy-Item (Join-Path $Root "data\urdu") (Join-Path $dataDest "urdu") -Recurse -Force

$manifestPath = Join-Path $Payload "AppxManifest.xml"
[xml]$manifest = Get-Content $manifestPath
$manifest.Package.Identity.Version = $Version
$manifest.Save($manifestPath)

$MsixPath = Join-Path $Root "dist\WordOnAirSlides_$Version`_x64.msix"
$makeAppx = Get-ChildItem "C:\Program Files (x86)\Windows Kits\10\bin\*\x64\makeappx.exe" -ErrorAction SilentlyContinue |
    Sort-Object FullName -Descending |
    Select-Object -First 1

if ($makeAppx) {
    Write-Host "Packing MSIX with $($makeAppx.FullName)"
    & $makeAppx.FullName pack /d $Payload /p $MsixPath /o
    Write-Host "MSIX ready: $MsixPath"
} else {
    Write-Warning "makeappx.exe not found. The payload folder is ready at $Payload"
}

Write-Host "Upload the .msix in Partner Center. Microsoft signs Store packages."
