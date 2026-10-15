# PowerShell runner script for sdn-selfheal in WSL
param (
    [Parameter(Position=0)]
    [string]$Target = "test"
)

$WSL_DIR = "/mnt/c/Users/Yashas Vishwakarma/Desktop/cn/sdn-selfheal"

Write-Host ">>> Running '$Target' inside Ubuntu WSL ($WSL_DIR)..." -ForegroundColor Cyan

switch ($Target) {
    "setup" {
        wsl -d Ubuntu bash -c "cd '$WSL_DIR' && make setup"
    }
    "test" {
        wsl -d Ubuntu bash -c "cd '$WSL_DIR' && make test"
    }
    "run-matrix" {
        wsl -d Ubuntu bash -c "cd '$WSL_DIR' && make run-matrix"
    }
    "analyze" {
        wsl -d Ubuntu bash -c "cd '$WSL_DIR' && make analyze"
    }
    "clean" {
        wsl -d Ubuntu bash -c "cd '$WSL_DIR' && make clean"
    }
    default {
        wsl -d Ubuntu bash -c "cd '$WSL_DIR' && make $Target"
    }
}
