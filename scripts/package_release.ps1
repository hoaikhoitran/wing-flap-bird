# Dong goi ban release: copy docs vao dist\WingFlapBird roi nen ZIP.
# Ket qua: release\WingFlapBird-v<version>-Windows-x64.zip
# Kiem tra: khong chua .venv / __pycache__ / .env / secret.
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

$py = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $py)) { $py = "python" }
$version = & $py -c "from core.version import APP_VERSION; print(APP_VERSION)"
if (-not $version) { throw "Khong doc duoc APP_VERSION" }

$distDir = "dist\WingFlapBird"
if (-not (Test-Path "$distDir\WingFlapBird.exe")) {
    throw "Chua co $distDir\WingFlapBird.exe - chay build truoc."
}

# --- Copy docs (duoi dang .txt de nguoi dung mo bang Notepad) ---
Copy-Item "LICENSE" "$distDir\LICENSE.txt" -Force
Copy-Item "PRIVACY.md" "$distDir\PRIVACY.txt" -Force
Copy-Item "THIRD_PARTY_NOTICES.md" "$distDir\THIRD_PARTY_NOTICES.txt" -Force
Copy-Item "docs\README_PLAYER.txt" "$distDir\README.txt" -Force

# --- Kiem tra noi dung cam ---
$forbidden = Get-ChildItem $distDir -Recurse -Force |
    Where-Object { $_.Name -match "^(\.venv|__pycache__|\.env|.*\.pyc)$" }
if ($forbidden) {
    $forbidden | ForEach-Object { Write-Host "CAM: $($_.FullName)" }
    throw "Ban build chua file khong duoc phep."
}

# --- Nen ZIP ---
New-Item -ItemType Directory -Force "release" | Out-Null
$zipName = "release\WingFlapBird-v$version-Windows-x64.zip"
if (Test-Path $zipName) { Remove-Item $zipName -Force }
Compress-Archive -Path $distDir -DestinationPath $zipName
Write-Host "Da tao $zipName"
Get-Item $zipName | Select-Object Name, @{n="SizeMB";e={[math]::Round($_.Length/1MB,1)}}
