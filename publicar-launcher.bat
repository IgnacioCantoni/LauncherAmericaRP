@echo off
rem Escribe launcher\version.txt con la version y la huella del AmericaRP.exe recien compilado.
rem Antes de subirlo, el .exe tiene que estar en la Release de GitHub con la etiqueta v + la version (ver README).
cd /d "%~dp0"
if not exist AmericaRP.exe (echo Primero corre compilar.bat & pause & exit /b 1)
AmericaRP.exe --publicar
type launcher\version.txt
pause
