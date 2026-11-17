<#
.SYNOPSIS
  Start the ACEsi server and open the ACEsi desktop window on the current code.

.DESCRIPTION
  This is what the desktop icon runs. Its one job is to make sure the window
  shows the same build as the browser version.

  Why it needs to do more than "start server, sleep, open window":

    * Windows lets a second process bind the same port (SO_REUSEADDR), so a
      second `python server.py` can sit next to the old one and requests land
      on either. That silently mixes old and new code - the "desktop is a few
      edits out" symptom.
    * server.py runs with debug=False, so a running process keeps the code it
      imported at boot. Only a replacement process picks up an edit.
    * A fixed Start-Sleep 6 races a slow boot; we wait for a real HTTP answer.
    * Every launch used to stack another pywebview window on top of the last.
    * WebView2 caches the document, so the window gets a cache-busted URL.

  A server is only replaced when it is actually stale (server.py,
  devtools_service.py or ace_config.yaml is newer than the process), so using
  the desktop icon does not interrupt an answer the browser is waiting for.
  Use -ForceRestart to replace it regardless.

  If the stale server was started as administrator, a normal shell cannot end
  it. You get one dialog offering to let Windows close it; say No and the
  launcher stops instead of opening a window on old code.

.EXAMPLE
  .\launch.ps1                 # what the desktop icon does (safe defaults)
  .\launch.ps1 -ForceRestart   # always replace the running server
  .\launch.ps1 -Gpu            # use hardware rendering instead of software

.NOTES
  Debugging needs no flag and nothing to remember: the desktop window always
  opens a localhost CDP endpoint on port 9222 so the ACEsi assistant can
  inspect the running page. That connection does NOT open a devtools window
  (the second WebView2 window that hard-reset this machine). F12 and Inspect
  stay disabled on purpose.
#>
[CmdletBinding()]
param(
  [int]$Port = 5000,
  [string]$Python = "$env:LOCALAPPDATA\Programs\Python\Python314\python.exe",
  [string]$Root,
  [switch]$ForceRestart,
  # Use GPU rendering for the window. Software rendering is the default: the
  # display driver on this machine times out several times a day, and the UI is
  # plain HTML, so the CPU compositor costs nothing visually.
  [switch]$Gpu
)

$ErrorActionPreference = 'Stop'

# $PSScriptRoot comes back empty in the param block under `powershell -File`,
# and the shortcut launches us exactly that way.
if (-not $Root) {
  $self = $MyInvocation.MyCommand.Path
  $Root = if ($self) { Split-Path -Parent $self } else { (Get-Location).Path }
}
Set-Location $Root

$Log = Join-Path $Root 'launch.log'
function Write-Log([string]$Message) {
  $line = "{0}  {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $Message
  try { Add-Content -LiteralPath $Log -Value $line -Encoding utf8 } catch { }
}

function Show-Dialog([string]$Message, [string]$Icon, [string]$Buttons = 'OK') {
  try {
    Add-Type -AssemblyName System.Windows.Forms
    # DefaultDesktopOnly keeps the box on the visible desktop and on top of it,
    # which a box owned by a hidden console otherwise fails to do.
    return [System.Windows.Forms.MessageBox]::Show(
      $Message,
      'ACEsi',
      [System.Windows.Forms.MessageBoxButtons]$Buttons,
      [System.Windows.Forms.MessageBoxIcon]$Icon,
      [System.Windows.Forms.MessageBoxDefaultButton]::Button1,
      [System.Windows.Forms.MessageBoxOptions]::DefaultDesktopOnly)
  } catch {
    Write-Log "dialog failed: $($_.Exception.Message)"
    return 'No'
  }
}

function Get-PortListeners {
  # netstat is used instead of Get-NetTCPConnection because that cmdlet
  # misattributes the owning process for locally-bound sockets.
  $pids = @()
  foreach ($row in (netstat -ano -p TCP)) {
    $f = @(($row -split '\s+') | Where-Object { $_ -ne '' })
    if ($f.Count -ge 5 -and $f[1] -match ":$Port$" -and $f[3] -eq 'LISTENING') {
      $pids += [int]$f[4]
    }
  }
  return @($pids | Sort-Object -Unique)
}

function Test-ServerUp {
  try {
    $r = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/" -UseBasicParsing -TimeoutSec 3
    return ($r.StatusCode -eq 200)
  } catch { return $false }
}

function Get-ServerProcesses {
  # Only python processes: the port may be owned by a server whose command line
  # is unreadable (elevated), which still counts, but nothing else is touched.
  $candidates = @(Get-PortListeners)
  $candidates += @(Get-CimInstance Win32_Process |
    Where-Object { $_.Name -match '^python' -and $_.CommandLine -match 'server\.py' } |
    ForEach-Object { [int]$_.ProcessId })

  $result = @()
  foreach ($p in ($candidates | Sort-Object -Unique)) {
    $proc = Get-Process -Id $p -ErrorAction SilentlyContinue
    if (-not $proc -or $proc.ProcessName -notmatch '^python') { continue }
    $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId=$p" -ErrorAction SilentlyContinue).CommandLine
    if ($cmdLine -and $cmdLine -notmatch 'server\.py') { continue }
    $result += $p
  }
  return @($result | Sort-Object -Unique)
}

function Wait-PortFree([int]$Tries = 40) {
  for ($i = 0; $i -lt $Tries; $i++) {
    if (-not (Get-PortListeners)) { return $true }
    Start-Sleep -Milliseconds 250
  }
  return (-not (Get-PortListeners))
}

try {

  if (-not (Test-Path -LiteralPath $Python)) {
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if (-not $cmd) { throw "python.exe not found at '$Python' and not on PATH." }
    $Python = $cmd.Source
  }

  $baseUrl = "http://127.0.0.1:$Port/"
  $stdout = Join-Path $Root 'server_stdout.txt'
  $stderr = Join-Path $Root 'server_stderr.txt'
  $appPy = Join-Path $Root 'desktop_app.py'

  # Inherited by the server and the window, so tracebacks never die on a
  # cp1252 encode error.
  $env:PYTHONIOENCODING = 'utf-8'
  $env:PYTHONUTF8 = '1'

  # ---- 1. is the running server stale? ------------------------------------
  $serverPids = @(Get-ServerProcesses)
  $listeners = @(Get-PortListeners)
  if ($listeners.Count -gt 1) {
    Write-Log "found $($listeners.Count) processes listening on port $Port ($($listeners -join ', ')) - duplicate servers, replacing"
  }

  if ($serverPids.Count -gt 0) {
    $oldest = ($serverPids |
      ForEach-Object { (Get-Process -Id $_ -ErrorAction SilentlyContinue).StartTime } |
      Where-Object { $_ } | Sort-Object | Select-Object -First 1)
    $newestSource = @('server.py', 'devtools_service.py', 'ace_config.yaml') |
      ForEach-Object { Get-Item -LiteralPath (Join-Path $Root $_) -ErrorAction SilentlyContinue } |
      Sort-Object LastWriteTime | Select-Object -Last 1
    $stale = $ForceRestart -or $listeners.Count -gt 1 -or ($oldest -and $newestSource -and $newestSource.LastWriteTime -gt $oldest)

    if ($stale) {
      $why = if ($ForceRestart) { '-ForceRestart' } elseif ($listeners.Count -gt 1) { 'duplicate listeners' } else { "$($newestSource.Name) is newer than pid $($serverPids -join ',')" }
      Write-Log "replacing server: $why"

      foreach ($p in $serverPids) {
        Write-Log "  stopping pid $p"
        Stop-Process -Id $p -Force -ErrorAction SilentlyContinue
      }
      $freed = Wait-PortFree

      if (-not $freed) {
        $held = (Get-PortListeners) -join ', '
        Write-Log "port $Port still held by $held - needs elevation"
        $answer = Show-Dialog (
          "An old ACEsi server is still running with administrator rights " +
          "(process $held), so the desktop window would open on old code.`n`n" +
          "Yes: let Windows close it now (a permission prompt appears).`n" +
          "No: leave everything as it is and do not open the window.") 'Warning' 'YesNo'
        if ($answer -ne 'Yes') {
          Write-Log "user declined the elevated stop"
          return
        }
        try {
          Start-Process -FilePath 'powershell.exe' -Verb RunAs -WindowStyle Hidden -Wait -ArgumentList @(
            '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command',
            "Stop-Process -Id $($serverPids -join ',') -Force -ErrorAction SilentlyContinue"
          ) | Out-Null
        } catch {
          Write-Log "elevated stop failed: $($_.Exception.Message)"
        }
        $freed = Wait-PortFree 80
        if (-not $freed) {
          Write-Log "ERROR: port $Port is still held after the elevated stop"
          Show-Dialog ("ACEsi could not free port $Port.`n`n" +
            "Open Task Manager, end the python.exe running as administrator, " +
            "then click the ACEsi icon again.") 'Error' | Out-Null
          return
        }
      }
      Write-Log "port $Port is free"
    } else {
      Write-Log "keeping running server pid $($serverPids -join ',') (it already has the current server code)"
    }
  }

  # ---- 2. start the server when nothing answers ---------------------------
  $serverProc = $null
  if (-not (Test-ServerUp)) {
    Write-Log "starting: $Python server.py (port $Port)"
    $serverProc = Start-Process -FilePath $Python -ArgumentList 'server.py' `
      -WorkingDirectory $Root `
      -RedirectStandardOutput $stdout `
      -RedirectStandardError $stderr `
      -WindowStyle Hidden -PassThru
  }

  # ---- 3. wait for a real answer, not a fixed sleep -----------------------
  $up = $false
  for ($i = 0; $i -lt 120; $i++) {
    if (Test-ServerUp) { $up = $true; break }
    Start-Sleep -Milliseconds 500
  }
  if (-not $up) {
    $tail = if (Test-Path -LiteralPath $stderr) { (Get-Content -LiteralPath $stderr -Tail 15) -join ' | ' } else { '(no stderr)' }
    Write-Log "ERROR: $baseUrl did not answer within 60s. $tail"
    Show-Dialog "The ACEsi server did not start on port $Port.`nSee launch.log and server_stderr.txt." 'Error' | Out-Null
    return
  }

  # ---- 4. prove the window will talk to the server we just started -------
  $owners = @(Get-PortListeners)
  if ($owners.Count -ne 1) {
    Write-Log "WARNING: port $Port has $($owners.Count) listeners ($($owners -join ', '))"
  } elseif ($serverProc -and $owners[0] -ne $serverProc.Id) {
    Write-Log "WARNING: port $Port is answered by pid $($owners[0]), not the server we started (pid $($serverProc.Id))"
  } else {
    Write-Log "server is up on $baseUrl (pid $($owners -join ','))"
  }

  try {
    $served = (New-Object System.Net.WebClient).DownloadData($baseUrl)
    $sha = [System.Security.Cryptography.SHA256]::Create()
    $servedHash = ([BitConverter]::ToString($sha.ComputeHash($served)) -replace '-', '')
    $diskHash = (Get-FileHash -LiteralPath (Join-Path $Root 'ACEsi.html') -Algorithm SHA256).Hash
    if ($servedHash -ne $diskHash) {
      Write-Log "WARNING: served ACEsi.html differs from $Root\ACEsi.html - another checkout answers on port $Port"
    } else {
      Write-Log "served ACEsi.html matches the file on disk"
    }
  } catch {
    Write-Log "WARNING: could not compare served HTML: $($_.Exception.Message)"
  }

  # ---- 5. close the previous desktop window so they do not stack ---------
  $oldWindows = @(Get-CimInstance Win32_Process |
    Where-Object { $_.Name -match '^python' -and $_.CommandLine -match 'desktop_app\.py|webview\.create_window' })
  foreach ($w in $oldWindows) {
    Write-Log "closing previous desktop window pid $($w.ProcessId)"
    Stop-Process -Id $w.ProcessId -Force -ErrorAction SilentlyContinue
  }
  if ($oldWindows.Count -gt 0) { Start-Sleep -Milliseconds 400 }

  # ---- 6. open the window ------------------------------------------------
  $desktopArgs = '"{0}" --port {1}' -f $appPy, $Port
  if ($Gpu) { $desktopArgs += ' --gpu' }
  Write-Log "opening desktop window: $desktopArgs"
  # python.exe is a console program: launching it pops a black console window
  # behind the app. -WindowStyle Hidden is not an option either - Windows
  # applies SW_HIDE to the process's first ShowWindow call, which is the
  # pywebview window, so the app would start invisible. pythonw.exe is the GUI
  # build of the same interpreter: no console, and a normal window.
  $windowExe = Join-Path (Split-Path -Parent $Python) 'pythonw.exe'
  if (-not (Test-Path $windowExe)) {
    Write-Log "WARNING: $windowExe not found, falling back to python.exe (a console window will show)"
    $windowExe = $Python
  }
  $win = Start-Process -FilePath $windowExe -ArgumentList $desktopArgs -WorkingDirectory $Root `
    -RedirectStandardOutput (Join-Path $Root 'desktop_stdout.log') `
    -RedirectStandardError (Join-Path $Root 'desktop_stderr.log') `
    -PassThru

  for ($i = 0; $i -lt 80; $i++) {
    if ($win.HasExited) {
      Write-Log "ERROR: desktop window exited immediately (code $($win.ExitCode))"
      Show-Dialog "The ACEsi desktop window failed to start. See launch.log." 'Error' | Out-Null
      return
    }
    $win.Refresh()
    if ($win.MainWindowHandle -ne 0) { break }
    Start-Sleep -Milliseconds 250
  }
  Write-Log "desktop window pid $($win.Id) is open"

}
catch {
  # The shortcut runs this hidden, so an unhandled error would vanish.
  Write-Log "FATAL: $($_.Exception.Message)"
  Show-Dialog "ACEsi could not start:`n`n$($_.Exception.Message)`n`nDetails are in launch.log." 'Error' | Out-Null
}
