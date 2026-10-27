$startTime = Get-Date

py -3.14 -m venv venv
.\venv\Scripts\Activate.ps1
python.exe -m pip install --upgrade pip
pip install -r requirements.txt
pip install nuitka==4.3.1

Set-Content -Path ".\buildtime.py" -Value "buildTime = '$(Get-Date -Format 'yyyyMMdd_HHmmss')'" -Encoding UTF8

$env:CL = "/utf-8"

python -m nuitka --standalone `
--windows-console-mode=disable `
--lto=yes `
--no-deployment-flag=self-contained `
--enable-plugin=tk-inter `
--include-package-data=tkinterdnd2 `
--windows-company-name="IYATT-yx" `
--windows-product-name="文件占用查询与解除工具" `
--windows-file-description="文件占用查询与解除工具" `
--windows-product-version="1.0.0.0" `
--windows-file-version="1.0.0.0" `
--copyright="Copyright (C) 2026 IYATT-yx. All Rights Reserved." `
--windows-icon-from-ico=.\icon.ico `
--include-data-file=.\icon.ico=.\ `
--output-dir=dist `
--output-filename=FileUnlocker_win_amd64 `
.\FileUnlocker.py

if (Test-Path "dist\FileUnlocker.dist")
{
    if (Test-Path "dist\FileUnlocker_win_amd64")
    {
        Remove-Item -Path "dist\FileUnlocker_win_amd64" -Recurse -Force
    }
    Rename-Item -Path "dist\FileUnlocker.dist" -NewName "FileUnlocker_win_amd64"
}

$endTime = Get-Date
$elapsedTime = New-TimeSpan -Start $startTime -End $endTime
Write-Output "程序构建用时：$($elapsedTime.TotalSeconds) 秒"