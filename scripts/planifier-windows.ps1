# Planifie l'agent quotidien à 6h30 (heure locale) chaque jour
# Exécuter en PowerShell ADMINISTRATEUR :
#   Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
#   .\scripts\planifier-windows.ps1

$TaskName = "AgentQuotidien-DieuMerci"
$ProjectRoot = Split-Path $PSScriptRoot -Parent
$Python = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $Python) {
    $Python = (Get-Command py -ErrorAction SilentlyContinue).Source
    if ($Python) { $Python = "py" }
}

if (-not $Python) {
    Write-Error "Python introuvable. Installez Python 3.10+ depuis python.org"
    exit 1
}

$Script = Join-Path $ProjectRoot "src\run_daily.py"
$Action = New-ScheduledTaskAction -Execute $Python -Argument "`"$Script`" --mode cloud" -WorkingDirectory $ProjectRoot
$Trigger = New-ScheduledTaskTrigger -Daily -At "06:30"
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# Charger CURSOR_API_KEY depuis .env si présent
$EnvFile = Join-Path $ProjectRoot ".env"
if (Test-Path $EnvFile) {
    Get-Content $EnvFile | ForEach-Object {
        if ($_ -match '^\s*CURSOR_API_KEY\s*=\s*(.+)\s*$') {
            $env:CURSOR_API_KEY = $Matches[1].Trim().Trim('"')
        }
    }
}

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Force `
    -Description "Briefing quotidien Kawa Kanzururu + INVESTEE-GROUP via Cursor Cloud Agent"

Write-Host "Tâche planifiée : $TaskName — tous les jours à 6h30"
Write-Host "Test manuel : cd $ProjectRoot ; python src\run_daily.py"
