# ===========================================================
# setup_scheduler.ps1
# יוצר 3 משימות מתוזמנות ב-Windows Task Scheduler
# הרץ פעם אחת כמנהל מערכת (Run as Administrator)
# ===========================================================

param(
    [string]$PythonPath = "python",
    [string]$BotDir = $PSScriptRoot
)

$ScriptPath = Join-Path $BotDir "main.py"

$tasks = @(
    @{ Name = "BowlingBot_Morning";   Slot = 0; Hour = 9;  Minute = 0  },
    @{ Name = "BowlingBot_Afternoon"; Slot = 1; Hour = 13; Minute = 0  },
    @{ Name = "BowlingBot_Evening";   Slot = 2; Hour = 19; Minute = 0  }
)

foreach ($task in $tasks) {
    $trigger  = New-ScheduledTaskTrigger -Daily -At "$($task.Hour):$($task.Minute)"
    $action   = New-ScheduledTaskAction `
        -Execute $PythonPath `
        -Argument "`"$ScriptPath`" --slot $($task.Slot)" `
        -WorkingDirectory $BotDir
    $settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 5)

    Register-ScheduledTask `
        -TaskName $task.Name `
        -Trigger $trigger `
        -Action $action `
        -Settings $settings `
        -RunLevel Highest `
        -Force | Out-Null

    Write-Host "Created: $($task.Name) at $($task.Hour):$('{0:D2}' -f $task.Minute)" -ForegroundColor Green
}

Write-Host "`nDone! 3 tasks registered. Check Task Scheduler to verify." -ForegroundColor Cyan
