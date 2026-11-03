@echo off
rem Arma actualizaciones\manifiesto.txt con lo que haya en actualizaciones\archivos.
cd /d "%~dp0"
if not exist AmericaRP.exe (echo Primero corre compilar.bat & pause & exit /b 1)
if not exist actualizaciones\archivos mkdir actualizaciones\archivos
AmericaRP.exe --manifiesto actualizaciones\archivos
type actualizaciones\manifiesto.txt
pause
