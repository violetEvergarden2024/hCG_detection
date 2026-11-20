# -*- coding: utf-8 -*-
"""把启动脚本写成 cmd 能正确读取的编码（GBK + CRLF）"""
import os

BAT = r"""@echo off
chcp 936 >nul
title 滤纸片 RGB 自动识别
cd /d "%~dp0"
setlocal enabledelayedexpansion

set "PYEXE="
set "PYARGS="

rem ---- 1) 同目录下的 python路径.txt ----
if exist "%~dp0python路径.txt" (
    set /p USERPY=<"%~dp0python路径.txt"
    if defined USERPY if exist "!USERPY!" (
        set "PYEXE=!USERPY!"
        goto run
    )
)

rem ---- 2) PATH 里的 py / python ----
where py >nul 2>nul
if not errorlevel 1 (
    set "PYEXE=py"
    set "PYARGS=-3"
    goto run
)
where python >nul 2>nul
if not errorlevel 1 (
    set "PYEXE=python"
    goto run
)

rem ---- 3) DSH 运行时 ----
if exist "%USERPROFILE%\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe" (
    set "PYEXE=%USERPROFILE%\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"
    goto run
)

rem ---- 4) 常见安装目录 ----
if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" set "PYEXE=%LOCALAPPDATA%\Programs\Python\Python313\python.exe" & goto run
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set "PYEXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe" & goto run
if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" set "PYEXE=%LOCALAPPDATA%\Programs\Python\Python311\python.exe" & goto run
if exist "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" set "PYEXE=%LOCALAPPDATA%\Programs\Python\Python310\python.exe" & goto run
if exist "%USERPROFILE%\anaconda3\python.exe" set "PYEXE=%USERPROFILE%\anaconda3\python.exe" & goto run
if exist "%USERPROFILE%\miniconda3\python.exe" set "PYEXE=%USERPROFILE%\miniconda3\python.exe" & goto run

echo.
echo [错误] 没有找到可用的 Python 解释器。
echo.
echo   解决办法（任选其一）：
echo     1) 安装 Python： https://www.python.org/downloads/   安装时勾选 Add to PATH
echo     2) 在本目录下新建文本文件「python路径.txt」，写入 python.exe 的完整路径，例如：
echo        C:\Users\你的用户名\anaconda3\python.exe
echo.
pause
exit /b 1

:run
echo 使用解释器: %PYEXE% %PYARGS%

%PYEXE% %PYARGS% -c "import numpy, PIL" >nul 2>nul
if errorlevel 1 (
    echo 正在安装依赖 numpy / pillow ...
    %PYEXE% %PYARGS% -m pip install --quiet numpy pillow
    %PYEXE% %PYARGS% -c "import numpy, PIL" >nul 2>nul
    if errorlevel 1 (
        echo [错误] 依赖安装失败，请手动执行： %PYEXE% %PYARGS% -m pip install numpy pillow
        pause
        exit /b 1
    )
)

%PYEXE% %PYARGS% -c "import openpyxl" >nul 2>nul
if errorlevel 1 (
    echo 正在安装依赖 openpyxl （导出 Excel 用，可跳过） ...
    %PYEXE% %PYARGS% -m pip install --quiet openpyxl
)

%PYEXE% %PYARGS% app.py
if errorlevel 1 (
    echo.
    echo 运行出错，请把上面的提示发给我。
    pause
)
endlocal
exit /b 0
"""

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "启动滤纸片RGB识别.bat")
data = BAT.replace("\n", "\r\n").encode("gbk", errors="replace")
with open(path, "wb") as f:
    f.write(data)
print("written:", path, len(data), "bytes")
