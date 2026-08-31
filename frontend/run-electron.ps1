$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $MyInvocation.MyCommand.Path)

$electronPath = Join-Path $PWD 'node_modules/electron/dist/electron.exe'
if (-not (Test-Path $electronPath)) {
  Write-Host 'Electron runtime is missing. Repairing frontend dependencies...' -ForegroundColor Yellow
  bun run electron:repair
}

if (-not (Test-Path $electronPath)) {
  throw 'Electron runtime is still missing after dependency repair. Check Bun network/install errors.'
}

bun run electron:dev
