# One-click LaTeX Compilation Script for Windows
# Uses the portable standalone Tectonic compiler downloaded in TEMP

$tectonic = "$env:TEMP\tectonic_bin\tectonic.exe"
if (-not (Test-Path $tectonic)) {
    Write-Host "[INFO] Downloading portable LaTeX engine..." -ForegroundColor Cyan
    $url = "https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic%400.17.0/tectonic-0.17.0-x86_64-pc-windows-msvc.zip"
    $zipPath = "$env:TEMP\tectonic.zip"
    $destDir = "$env:TEMP\tectonic_bin"
    New-Item -ItemType Directory -Force -Path $destDir | Out-Null
    curl.exe -sL $url -o $zipPath
    Expand-Archive -Path $zipPath -DestinationPath $destDir -Force
}

Write-Host "[BUILD] Compiling main.tex (25-Page Formal VIT Research Project Report)..." -ForegroundColor Yellow
& $tectonic main.tex

Write-Host "[BUILD] Compiling main_ieee_transactions.tex (IEEE Transactions 2-Column Manuscript)..." -ForegroundColor Yellow
& $tectonic main_ieee_transactions.tex

Write-Host "[SUCCESS] Compilation complete! PDFs generated:" -ForegroundColor Green
Get-ChildItem *.pdf | Select-Object Name, Length, LastWriteTime
