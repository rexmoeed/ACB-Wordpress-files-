$ErrorActionPreference = 'Stop'
$auth = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes('admin:XFxg 7dCD 7FE9 7K3z W6mN 5FIh'))
$headers = @{ Authorization = "Basic $auth"; 'Content-Type' = 'application/json; charset=utf-8' }

$json = Get-Content 'e:\America Custom Boxes\acb_category_docs_extract.json' -Raw -Encoding UTF8 | ConvertFrom-Json

function Get-CategoryBlocks($paras) {
    $blocks = @{}
    $current = $null
    $currentParas = @()
    foreach ($p in $paras) {
        if ($p -match '^ACB CATEGORY PAGE') {
            if ($current) { $blocks[$current] = @($currentParas) }
            switch -Regex ($p) {
                'COSMETICS' { $current = 'cosmetics' }
                'FOOD' { $current = 'food' }
                'POPCORN' { $current = 'popcorn-boxes' }
                'BAKERY' { $current = 'bakery-boxes' }
                'CANDLE' { $current = 'candle-boxes' }
                'EVENT' { $current = 'event-boxes' }
                'MAILER' { $current = 'mailer-boxes' }
                'PRODUCT BOXES' { $current = 'product-boxes' }
                'TUCK' { $current = 'tuck-boxes' }
                'POD' { $current = 'pod-boxes' }
                'PHARMA' { $current = 'pharmaceutical-boxes' }
                'PET' { $current = 'pet-boxes' }
                default { $current = $null }
            }
            $currentParas = @()
            continue
        }
        if ($current) { $currentParas += $p }
    }
    if ($current) { $blocks[$current] = @($currentParas) }
    return $blocks
}

function Parse-Meta($paras) {
    $meta = @{ title = ''; description = ''; focuskw = '' }
    foreach ($p in $paras) {
        if ($p -match '^SEO Meta Title:\s*(.+)') { $meta.title = $Matches[1].Trim() }
        elseif ($p -match '^Meta Description:\s*(.+)') { $meta.description = $Matches[1].Trim() }
        elseif ($p -match '^Primary Keyword:\s*(.+)') { $meta.focuskw = $Matches[1].Trim() }
    }
    return $meta
}

function Build-ArchiveHtml($paras) {
    $stopHeaders = @('Industries Served','Applications','Available Box','Packaging Specification','Our Manufacturing Process','Quality Assurance','FAQ')
    $introParas = @()
    $whyTitle = ''
    $whyItems = @()
    $benTitle = ''
    $benefitItems = @()
    $mode = 'none'
    foreach ($p in $paras) {
        if ($stopHeaders -contains $p) { break }
        if ($p -eq 'Introduction') { $mode = 'intro'; continue }
        if ($p -match '^Why Choose') { $mode = 'why'; $whyTitle = $p; continue }
        if ($p -eq 'Key Benefits') { $mode = 'benefits'; $benTitle = $p; continue }
        if ($p -match '^(SEO Meta Title|Meta Description|URL Slug|Primary Keyword|Secondary Keywords|LSI Keywords|Long-Tail Keywords|Commercial Keywords|Transactional Keywords|Search Intent|Target Market|H1:|Hero Description|Get a Quote|THE VERTEX|SEO & On-Page|ACB CATEGORY|Packaging That Keeps|Food-grade, grease-resistant|Get a Quote  )') { continue }
        switch ($mode) {
            'intro' { if ($p.Length -gt 50) { $introParas += $p } }
            'why' {
                if ($p -match '^(.+?) [\u2014\u2013-] (.+)$') { $whyItems += "$($Matches[1]) - $($Matches[2])" }
            }
            'benefits' {
                if ($p -match '^(.+?) [\u2014\u2013-] (.+)$') { $benefitItems += "$($Matches[1]) - $($Matches[2])" }
                if ($benefitItems.Count -ge 6) { break }
            }
        }
    }
    $parts = @()
    if ($introParas.Count) { $parts += ($introParas -join "`n`n") }
    if ($whyItems.Count) {
        $parts += $whyTitle
        $parts += $whyItems
    }
    if ($benefitItems.Count) {
        $parts += $benTitle
        $parts += $benefitItems
    }
    return ($parts -join "`n")
}

$slugToId = @{
    'popcorn-boxes' = 38; 'bakery-boxes' = 27; 'candle-boxes' = 24; 'event-boxes' = 40
    'mailer-boxes' = 26; 'tuck-boxes' = 39; 'pet-boxes' = 33
}

$allBlocks = @{}
foreach ($prop in $json.PSObject.Properties) {
    foreach ($entry in (Get-CategoryBlocks $prop.Value).GetEnumerator()) {
        if (-not $allBlocks.ContainsKey($entry.Key)) { $allBlocks[$entry.Key] = $entry.Value }
    }
}

$results = @()
foreach ($entry in $slugToId.GetEnumerator()) {
    $slug = $entry.Key; $id = $entry.Value
    if (-not $allBlocks.ContainsKey($slug)) { Write-Host "SKIP $slug"; continue }
    $paras = $allBlocks[$slug]
    $meta = Parse-Meta $paras
    $html = Build-ArchiveHtml $paras

    $payload = [ordered]@{
        description = $html
        meta = [ordered]@{
            wpseo_title = $meta.title
            wpseo_metadesc = $meta.description
            wpseo_focuskw = $meta.focuskw
        }
    }
    $bytes = [System.Text.Encoding]::UTF8.GetBytes(($payload | ConvertTo-Json -Depth 6 -Compress))
    Invoke-RestMethod -Method POST -Uri "https://americacustomboxes.com/wp-json/wp/v2/product_cat/$id" -Headers $headers -Body $bytes | Out-Null
    Write-Host "OK $slug ($id)"
    $results += [PSCustomObject]@{ slug = $slug; id = $id; title = $meta.title; focuskw = $meta.focuskw; htmlLen = $html.Length }
}
$results | Format-Table -AutoSize
$results | ConvertTo-Json | Set-Content 'e:\America Custom Boxes\deploy_results.json' -Encoding utf8
