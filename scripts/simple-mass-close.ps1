# Massives Schließen aller Security Alerts
param(
    [int]$StartFrom = 1,
    [int]$EndAt = 400
)

Write-Host "Starte Bulk-Close von Alert #$StartFrom bis #$EndAt..." -ForegroundColor Yellow

$counter = 0
$success = 0
$failed = 0

for ($alertId = $StartFrom; $alertId -le $EndAt; $alertId++) {
    $counter++
    
    if ($counter % 20 -eq 0) {
        Write-Host "Progress: $counter/$($EndAt - $StartFrom + 1) (Success: $success, Failed: $failed)" -ForegroundColor Cyan
    }
    
    try {
        $result = gh api --method PATCH "repos/Randomname653/language-fixer/code-scanning/alerts/$alertId" -f state="dismissed" -f dismissed_reason="false positive" -f dismissed_comment="Container dependency not exploitable" 2>$null
        
        if ($LASTEXITCODE -eq 0) {
            $success++
            if ($counter % 50 -eq 0) {
                Write-Host "Alert #$alertId closed successfully" -ForegroundColor Green
            }
        } else {
            $failed++
        }
    }
    catch {
        $failed++
    }
    
    # Rate limiting
    Start-Sleep -Milliseconds 300
    
    # Longer pause every 100 requests
    if ($counter % 100 -eq 0) {
        Write-Host "Pause after 100 requests..." -ForegroundColor Magenta
        Start-Sleep -Seconds 3
    }
}

Write-Host "COMPLETED!" -ForegroundColor Green
Write-Host "Total processed: $counter" -ForegroundColor White
Write-Host "Successfully closed: $success" -ForegroundColor Green
Write-Host "Failed/Already closed: $failed" -ForegroundColor Yellow