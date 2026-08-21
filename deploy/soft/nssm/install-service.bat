@echo off
REM ============================================================
REM hz-dream Windows 服务一键安装（需管理员权限）
REM ============================================================
setlocal enabledelayedexpansion

echo.
echo === hz-dream 服务安装 ===
echo.

REM --- 1. 检查管理员权限 ---
net session >nul 2>&1
if errorlevel 1 (
    echo [错误] 需要管理员权限，请右键"以管理员身份运行"
    pause
    exit /b 1
)

REM --- 2. 定位 nssm.exe ---
set "NSSM="
where nssm >nul 2>&1 && set "NSSM=nssm"
if not defined NSSM (
    if exist "C:\nssm\nssm.exe" set "NSSM=C:\nssm\nssm.exe"
)
if not defined NSSM (
    if exist "%~dp0nssm.exe" set "NSSM=%~dp0nssm.exe"
)
if not defined NSSM (
    echo [错误] 找不到 nssm.exe
    echo        请从 https://nssm.cc/download 下载，解压后任选其一：
    echo          - 放到 C:\nssm\nssm.exe
    echo          - 放到本脚本同目录（deploy\）
    echo          - 或加入系统 PATH
    pause
    exit /b 1
)
echo [OK] nssm: %NSSM%

REM --- 3. 定位 javaw.exe ---
set "JAVAW="
if defined JAVA_HOME (
    if exist "%JAVA_HOME%\bin\javaw.exe" set "JAVAW=%JAVA_HOME%\bin\javaw.exe"
)
if not defined JAVAW (
    for /f "delims=" %%I in ('where javaw 2^>nul') do (
        set "JAVAW=%%I"
        goto :foundJava
    )
)
:foundJava
if not defined JAVAW (
    if exist "C:\Program Files\Java\jdk-11\bin\javaw.exe" set "JAVAW=C:\Program Files\Java\jdk-11\bin\javaw.exe"
)
if not defined JAVAW (
    if exist "C:\Program Files\Java\jre-11\bin\javaw.exe" set "JAVAW=C:\Program Files\Java\jre-11\bin\javaw.exe"
)
if not defined JAVAW (
    echo [错误] 找不到 javaw.exe
    echo        请确认 JDK/JRE 已安装，或设置 JAVA_HOME 环境变量
    pause
    exit /b 1
)
echo [OK] javaw: %JAVAW%

REM --- 4. 部署目录（脚本在 deploy\soft\nssm\，上溯两级回 deploy\）---
set "DEPLOY=%~dp0.."
pushd "%DEPLOY%"
set "DEPLOY=%CD%"
popd
set "JAR=%DEPLOY%\hz-dream.jar"
set "LOGDIR=%DEPLOY%\logs"
if not exist "%LOGDIR%" mkdir "%LOGDIR%"
echo [OK] deploy: %DEPLOY%

REM --- 5. 若已存在则先移除 ---
"%NSSM%" stop hz-dream >nul 2>&1
"%NSSM%" remove hz-dream confirm >nul 2>&1

REM --- 6. 注册服务 ---
"%NSSM%" install hz-dream "%JAVAW%"
if errorlevel 1 (
    echo [错误] 服务注册失败
    pause
    exit /b 1
)

REM --- 7. 配置 ---
"%NSSM%" set hz-dream AppDirectory "%DEPLOY%"
"%NSSM%" set hz-dream AppParameters "-jar \"%JAR%\""
"%NSSM%" set hz-dream AppStdout "%LOGDIR%\app.log"
"%NSSM%" set hz-dream AppStderr "%LOGDIR%\app.log"
"%NSSM%" set hz-dream AppRotateFiles 1
"%NSSM%" set hz-dream AppRotateBytes 10485760
"%NSSM%" set hz-dream AppRotateBackups 5
"%NSSM%" set hz-dream AppExit Default Restart
"%NSSM%" set hz-dream AppRestartDelay 5000
"%NSSM%" set hz-dream Start SERVICE_AUTO_START
"%NSSM%" set hz-dream Description "hz-dream Spring Boot 应用"
"%NSSM%" set hz-dream DisplayName "hz-dream"

REM --- 8. 启动 ---
"%NSSM%" start hz-dream
if errorlevel 1 (
    echo [警告] 服务启动失败，请用 services.msc 查看错误
    pause
    exit /b 1
)

echo.
echo === 安装完成 ===
echo 服务名: hz-dream
echo 启动类型: 开机自动启动
echo 日志文件: %LOGDIR%\app.log
echo 访问地址: http://localhost:8080
echo.
echo 管理命令:
echo   停止: nssm stop hz-dream
echo   启动: nssm start hz-dream
echo   重启: nssm restart hz-dream
echo   状态: nssm status hz-dream
echo   卸载: nssm remove hz-dream confirm
echo.
pause