# Deploy archive layout + styled content snippets to LIVE
$ErrorActionPreference = 'Stop'

if (-not $env:ACB_WP_APP_PASS) {
    Write-Error 'Set ACB_WP_APP_PASS environment variable to the WordPress application password.'
}

$auth = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("admin:$($env:ACB_WP_APP_PASS)"))
$headers = @{ Authorization = "Basic $auth"; 'Content-Type' = 'application/json; charset=utf-8' }

# Update snippet #15 (layout CSS)
$layout = Get-Content 'e:\America Custom Boxes\archive-layout-snippet.json' -Raw -Encoding UTF8 | ConvertFrom-Json
$layoutBody = [System.Text.Encoding]::UTF8.GetBytes(($layout | ConvertTo-Json -Depth 5 -Compress))
$layoutResp = Invoke-RestMethod -Method PUT -Uri 'https://americacustomboxes.com/wp-json/code-snippets/v1/snippets/15' -Headers $headers -Body $layoutBody
Write-Host "Updated snippet #15: $($layoutResp.name) active=$($layoutResp.active)"

# Create or update snippet #17 (styled content) — try PUT first, POST if missing
$content = Get-Content 'e:\America Custom Boxes\archive-content-snippet.json' -Raw -Encoding UTF8 | ConvertFrom-Json
$contentBody = [System.Text.Encoding]::UTF8.GetBytes(($content | ConvertTo-Json -Depth 5 -Compress))
try {
    $contentResp = Invoke-RestMethod -Method PUT -Uri 'https://americacustomboxes.com/wp-json/code-snippets/v1/snippets/17' -Headers $headers -Body $contentBody
    Write-Host "Updated snippet #17: $($contentResp.name) active=$($contentResp.active)"
} catch {
    $contentResp = Invoke-RestMethod -Method POST -Uri 'https://americacustomboxes.com/wp-json/code-snippets/v1/snippets' -Headers $headers -Body $contentBody
    Write-Host "Created snippet #$($contentResp.id): $($contentResp.name) active=$($contentResp.active)"
}

Write-Host 'Done. Run deploy-categories-v2.ps1 to refresh category HTML if needed.'
