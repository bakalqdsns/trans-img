@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ============================================================
echo BallonsTranslator 启动脚本 (Windows)
echo ============================================================
echo.

:: 获取脚本所在目录
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."

:: 检查Python
echo 检查Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到Python
    echo 请安装Python 3.8或更高版本，并添加到PATH
    pause
    exit /b 1
)

for /f "tokens=2" %%a in ('python --version 2^>^&1') do set PYTHON_VERSION=%%a
echo Python版本: %PYTHON_VERSION%

:: 检查项目结构
echo.
echo 检查项目结构...
if not exist "%PROJECT_ROOT%\launch.py" (
    echo 错误: 未找到 launch.py
    echo 请确保在正确的目录中运行此脚本
    pause
    exit /b 1
)
echo [OK] 项目结构正常

:: 检查模型注册表
echo.
echo 检查模型注册表...
if exist "%PROJECT_ROOT%\config\custom_models" (
    set /a MODEL_COUNT=0
    for %%f in ("%PROJECT_ROOT%\config\custom_models\*.json") do set /a MODEL_COUNT+=1
    echo [OK] 找到 !MODEL_COUNT! 个自定义模型
) else (
    echo [!] 自定义模型目录不存在，运行配置脚本...
    python "%PROJECT_ROOT%\scripts\setup_quick.py"
)

:: 启动应用
echo.
echo ============================================================
echo 启动 BallonsTranslator...
echo ============================================================
echo.

cd /d "%PROJECT_ROOT%"
python launch.py %*

:: 检查退出状态
set EXIT_CODE=%errorlevel%
if %EXIT_CODE% neq 0 (
    echo.
    echo ============================================================
    echo 应用异常退出 (代码: %EXIT_CODE%)
    echo ============================================================
    
    if %EXIT_CODE% equ 1 (
        echo.
        echo 可能的解决方案:
        echo   1. 安装依赖: pip install -r requirements.txt
        echo   2. 运行配置: python scripts/setup_quick.py
        echo   3. 检查日志: 查看控制台输出
    )
    
    pause
    exit /b %EXIT_CODE%
)

echo.
echo ============================================================
echo 应用已关闭
echo ============================================================

pause
