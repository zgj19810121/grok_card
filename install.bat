@echo off
echo ========================================
echo   Installing dependencies / 安装依赖
echo ========================================
pip install -r requirements.txt
echo.
echo ========================================
echo   Installing browsers / 安装浏览器
echo ========================================
python -m patchright install chromium
python -m camoufox fetch
echo.
echo ========================================
echo   Done / 安装完成
echo ========================================
pause
