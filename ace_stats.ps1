# ACEsi dashboard stats (CPU / RAM). Run: powershell -NoProfile -File <this file>
# Output: "usedMB,cpuPct"
$os = Get-CimInstance Win32_OperatingSystem
$used = [math]::Round(($os.TotalVisibleMemorySize - $os.FreePhysicalMemory)/1024)
$cpu = [int]((Get-Counter '\Processor(_Total)\% Processor Time').CounterSamples[0].CookedValue)
Write-Output "$used,$cpu"
