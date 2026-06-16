@echo off
echo [*] Iniciando desinstalacao do Evil JWT Force...

echo [*] Executando script de desinstalacao Python...
python install_deps.py --uninstall

echo [*] Removendo diretorios...
rmdir /s /q logs output reports 2>nul

echo [*] Desinstalacao concluida!
pause 