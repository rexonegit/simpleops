@echo off
setlocal enabledelayedexpansion

echo ========================================
echo  Cleaning Django cache and migration files
echo ========================================

echo.
echo [1] Deleting all __pycache__ directories...
for /d /r . %%d in (__pycache__) do (
    if exist "%%d" (
        echo Removing "%%d"
        rmdir /s /q "%%d"
    )
)

echo.
echo [2] Deleting migration files (keeping __init__.py)...
for /d /r . %%d in (migrations) do (
    if exist "%%d" (
        pushd "%%d"
        for /f "delims=" %%f in ('dir /b *.py 2^>nul ^| findstr /r "^[0-9].*\.py$"') do (
            echo Deleting "%%d\%%f"
            del /q "%%f"
        )
        popd
    )
)

echo.
echo Done.
pause