@echo off
rem Compila el launcher con el compilador de C# que ya trae Windows (.NET Framework 4.x).
cd /d "%~dp0"
set CSC=%WINDIR%\Microsoft.NET\Framework64\v4.0.30319\csc.exe
if not exist "%CSC%" set CSC=%WINDIR%\Microsoft.NET\Framework\v4.0.30319\csc.exe
"%CSC%" /nologo /codepage:65001 /target:winexe /out:AmericaRP.exe /resource:fuentes\BebasNeue.ttf,BebasNeue.ttf /resource:fuentes\Barlow-Regular.ttf,Barlow-Regular.ttf /resource:fuentes\Barlow-Bold.ttf,Barlow-Bold.ttf /r:System.Windows.Forms.dll /r:System.Drawing.dll /r:System.Core.dll src\Launcher.cs
if errorlevel 1 (echo. & echo Hubo errores al compilar. & pause & exit /b 1)
echo Listo: AmericaRP.exe
pause
