@echo off
chcp 65001 >nul
cd /d "%~dp0"

where py >nul 2>&1
if errorlevel 1 (
    echo Python nao encontrado. Instale em python.org e marque "Add to PATH".
    pause
    exit /b 1
)

py -c "import pypdf, reportlab, PIL" >nul 2>&1
if errorlevel 1 (
    echo Instalando dependencias...
    py -m pip install pypdf reportlab pillow
    if errorlevel 1 (
        echo Falha ao instalar dependencias.
        pause
        exit /b 1
    )
)

if not exist "config.json" (
    echo config.json nao encontrado nesta pasta.
    pause
    exit /b 1
)

py inserir_assinatura.py --config config.json
echo.
pause
