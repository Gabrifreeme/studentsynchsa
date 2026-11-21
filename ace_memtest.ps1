$r = "none"
try { $os = Get-CimInstance Win32_OperatingSystem; $r = "cim: total=" + $os.TotalVisibleMemorySize + " free=" + $os.FreePhysicalMemory }
catch { $r = "cim ERR " + $_.Exception.Message }
Write-Output "A: " + $r

$r2 = "none"
try { $ci = Get-ComputerInfo; $r2 = "ci: total=" + $ci.CsTotalPhysicalMemory + " free=" + $ci.CsFreePhysicalMemory }
catch { $r2 = "ci ERR " + $_.Exception.Message }
Write-Output "B: " + $r2

$r3 = "none"
try { $w = Get-WmiObject Win32_OperatingSystem; $r3 = "wmi: total=" + $w.TotalVisibleMemorySize + " free=" + $w.FreePhysicalMemory }
catch { $r3 = "wmi ERR " + $_.Exception.Message }
Write-Output "C: " + $r3

$r4 = "none"
try { $out = & systeminfo 2>&1 | Where-Object { $_ -match "Total Physical Memory|Available Physical Memory" }; $r4 = "si: " + ($out -join " | ") }
catch { $r4 = "si ERR " + $_.Exception.Message }
Write-Output "D: " + $r4
