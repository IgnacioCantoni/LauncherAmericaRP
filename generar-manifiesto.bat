@echo off
rem Rehace los manifiestos con lo que haya en actualizaciones\archivos, en paquetes\enb\archivos y en mods\<id>\archivos.
cd /d "%~dp0"
if not exist AmericaRP.exe (echo Primero corre compilar.bat & pause & exit /b 1)
if not exist actualizaciones\archivos mkdir actualizaciones\archivos
if not exist paquetes\enb\archivos mkdir paquetes\enb\archivos
AmericaRP.exe --manifiesto actualizaciones\archivos
AmericaRP.exe --manifiesto paquetes\enb\archivos
for /d %%m in (mods\*) do if exist "%%m\archivos" AmericaRP.exe --manifiesto "%%m\archivos"
type actualizaciones\manifiesto.txt
type paquetes\enb\manifiesto.txt
pause
