Write-Host "Installing missing dependencies..." -ForegroundColor Green

# Check if virtual environment is activated
if (-not $env:VIRTUAL_ENV) {
    if (Test-Path "venv\Scripts\Activate.ps1") {
        Write-Host "Activating virtual environment..." -ForegroundColor Yellow
        & .\venv\Scripts\Activate.ps1
    }
}

Write-Host "Installing pandas and other missing dependencies..." -ForegroundColor Yellow

# Install specific missing packages
pip install pandas==2.1.4
pip install openpyxl==3.1.2
pip install python-docx==1.1.0
pip install PyPDF2==3.0.1

# Or install all requirements to be sure
Write-Host "`nInstalling all requirements to ensure nothing is missing..." -ForegroundColor Yellow
pip install -r requirements.txt

Write-Host "`n✅ Dependencies installed!" -ForegroundColor Green