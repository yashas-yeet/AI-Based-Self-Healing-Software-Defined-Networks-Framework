@echo off
set TARGET=%1
if "%TARGET%"=="" set TARGET=test
echo [SDN-SELFHEAL] Executing %TARGET% in Ubuntu WSL...
wsl -d Ubuntu bash -c "cd '/mnt/c/Users/Yashas Vishwakarma/Desktop/cn/sdn-selfheal' && make %TARGET%"
