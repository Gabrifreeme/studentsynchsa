<#
.SYNOPSIS
  Restart the ACEsi server and prove which code the new process loaded.

.DESCRIPTION
  server.py runs with no console (python.exe, output redirected, window
  hidden), so after a restart there is no visible sign that the edit was
  picked up. This script kills whatever holds port 5000, rotates the old logs,
  starts python.exe again with both streams redirected, waits for the port, and
  then prints the boot banner plus a stale/matching verdict.

  Log files written by the server:
    server_stdout.txt  - the app's own print() output, incl. the boot banner
    server_stderr.txt  - Werkzeug access log (noisy: the UI polls constantly)

.EXAMPLE
  .\restart_server.ps1
  .\restart_server.ps1 -Tail        # leave a live Get-Content -Wait open
#>
[CmdletBinding()]
param(
  [int]$Port = 5000,
  [string]$Python = "$env:LOCALAPPDATA\Programs\Python\Python314\python.exe",
  [string]$Root,
  [switch]$Tail,
  [switch]$NoRotate
)

$ErrorActionPreference = 'Stop'
# $PSScriptRoot is not reliably populated in the param block (it comes back
# empty under `powershell -File`), so resolve the repo root here instead.
if (-not $Root) {
  $self = $MyInvocation.MyCommand.Path
  $Root = if ($self) { Split-Path -Parent $self } else { (Get-Location).Path }
}
Set-Location $Root
$out = Join-Path $Root 'server_stdout.txt'
$err = Join-Path $Root 'server_stderr.txt'

function Stop-Listener {
  $conns = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
  if (-not $conns) { return @() }
  $pids = @($conns | ForEach-Object { $_.OwningProcess } | Sort-Object -Unique)
  foreach ($p in $pids) {
    Write-Host "  stopping pid $p (was holding port $Port)"
    Stop-Process -Id $p -Force -ErrorAction SilentlyContinue
  }
  # Give the socket a moment to actually clear before rebinding.
  for ($i = 0; $i -lt 40; $i++) {
    if (-not (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)) { break }
    Start-Sleep -Milliseconds 250
  }
  return $pids
}

Write-Host "==> stopping any listener on port $Port"
$old = Stop-Listener

# Stop-Process is deliberately quiet, so a refused stop (the server runs
# elevated and this shell does not) would otherwise look like success. Rotating
# logs here would then fail too, because the surviving process still holds them
# open - so say what actually happened and leave the working server alone.
$still = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if ($still) {
  $owner = ($still | Select-Object -First 1).OwningProcess
  Write-Host "!! port $Port is still held by pid $owner - the stop was refused." -ForegroundColor Red
  Write-Host "   That process is running elevated. End python.exe from Task Manager" -ForegroundColor Red
  Write-Host "   (Run as administrator), then start the server from a normal terminal." -ForegroundColor Red
  exit 1
}

if (-not $NoRotate) {
  # Append-only logs grow without bound (the access log alone hit 69 KB in
  # minutes), and a fresh file makes "is the banner there?" unambiguous.
  $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
  foreach ($f in @($out, $err)) {
    if (Test-Path $f) {
      $bak = "$f.$stamp"
      Move-Item -LiteralPath $f -Destination $bak -Force
      Write-Host "  rotated $(Split-Path $f -Leaf) -> $(Split-Path $bak -Leaf)"
    }
  }
}

Write-Host "==> starting: $Python server.py"
Write-Host "    stdout -> $out"
Write-Host "    stderr -> $err  (Werkzeug access log; app errors appear here too)"
# Belt and braces: server.py also forces UTF-8 on its own streams, but set it
# here too so anything it shells out to inherits it.
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'
$runStart = Get-Date
Start-Process -FilePath $Python -ArgumentList 'server.py' `
  -WorkingDirectory $Root `
  -RedirectStandardOutput $out `
  -RedirectStandardError $err `
  -WindowStyle Hidden | Out-Null

# Only accept a NEW process. A listener that survived Stop-Listener (because it
# runs elevated and this shell cannot stop it) must not be reported as "UP":
# that is exactly how a failed restart looked successful.
$new = $null
$blocker = $null
for ($i = 0; $i -lt 120; $i++) {
  $c = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
  if ($c) {
    $cand = $c[0].OwningProcess
    $candStart = (Get-Process -Id $cand -ErrorAction SilentlyContinue).StartTime
    if ($old -notcontains $cand -and $candStart -and $candStart -ge $runStart) {
      $new = $cand
      break
    }
    $blocker = $cand
  }
  Start-Sleep -Milliseconds 500
}

if (-not $new) {
  if ($blocker) {
    Write-Host "!! port $Port is still held by pid $blocker, which survived the stop." -ForegroundColor Red
    Write-Host "   It is probably running elevated; stop it from an elevated shell or Task Manager," -ForegroundColor Red
    Write-Host "   then start the server again from a normal (non-admin) terminal." -ForegroundColor Red
  } else {
    Write-Host "!! FAILED to bind port $Port within 60s. Last 20 stderr lines:" -ForegroundColor Red
    if (Test-Path $err) { Get-Content $err -Tail 20 | ForEach-Object { "   $_" } }
  }
  exit 1
}

$proc = Get-CimInstance Win32_Process -Filter "ProcessId=$new"
$started = (Get-Process -Id $new).StartTime
Write-Host "==> UP  pid $new  started $started"
Write-Host "    exe  $($proc.ExecutablePath)"

# Stale-code verdict: a source file edited AFTER the process started cannot
# be in the running process.
$stale = @()
foreach ($f in @('server.py', 'devtools_service.py', 'ace_config.yaml')) {
  $p = Join-Path $Root $f
  if (Test-Path $p) {
    $mt = (Get-Item $p).LastWriteTime
    if ($mt -gt $started) {
      $stale += "$f (mtime $mt > start $started)"
    }
  }
}
if ($stale) {
  Write-Host "!! STALE: edited after this process started:" -ForegroundColor Red
  $stale | ForEach-Object { Write-Host "     $_" -ForegroundColor Red }
  Write-Host "   run this script again." -ForegroundColor Red
} else {
  Write-Host "    OK: every source file predates this process, so the new code is loaded." -ForegroundColor Green
}

Write-Host ""
Write-Host "==> boot banner (from server_stdout.txt)"
if (Test-Path $out) {
  Get-Content $out -Tail 14 | ForEach-Object { "   $_" }
}
$banner = if (Test-Path $out) { Get-Content $out -Raw } else { '' }
$missing = @()
foreach ($tool in @('cdp_get_response_body', 'cdp_network_requests', 'cdp_navigate')) {
  if ($banner -notmatch [regex]::Escape($tool)) { $missing += $tool }
}
if ($missing) {
  Write-Host "!! banner does not mention: $($missing -join ', ')  <-- running OLD code" -ForegroundColor Red
} else {
  Write-Host "    banner lists the new CDP tools, so this process has them." -ForegroundColor Green
}

Write-Host ""
Write-Host "==> watch it yourself:"
Write-Host "    Get-Content '$out' -Wait -Tail 50      # app output + boot banner"
Write-Host "    Get-Content '$err' -Wait -Tail 20      # access log + tracebacks"

if ($Tail) {
  Write-Host ""
  Write-Host "==> streaming stdout (Ctrl+C to stop watching; server keeps running)"
  Get-Content $out -Wait -Tail 50
}
