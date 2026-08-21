@echo off
REM ============================================================
REM hz-dream Windows 服务卸载（需管理员权限）
REM ============================================================
setlocal

echo.
echo === hz-dream 服务卸载 ===
echo.

net session >nul 2>&1
if errorlevel 1 (
    echo [错误] 需要管理员权限
    pause
    exit /b 1
)

set "NSSM="
where nssm >nul 2>&1 && set "NSSM=nssm"
if not defined NSSM if exist "C:\nssm\nssm.exe" set "NSSM=C:\nssm\nssm.exe"
if not defined NSSM if exist "%~dp0nssm.exe" set "NSSM=%~dp0nssm.exe"
if not defined NSSM (
    echo [错误] 找不到 nssm.exe
    pause
    exit /b 1
)

"%NSSM%" stop hz-dream >nul 2>&1
echo 已停止服务
"%NSSM%" remove hz-dream confirm
echo.
echo === 卸载完成 ===
echo 日志目录 deploy\logs 保留，可手动删除
echo.
pause