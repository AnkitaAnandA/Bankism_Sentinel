$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not (Test-Path -LiteralPath ./.venv/Scripts/python.exe)) { throw 'Run .\Setup.ps1 first' }
& ./.venv/Scripts/python.exe scripts/run_local.py
