$ErrorActionPreference = 'Stop'
$auth = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes('admin:XFxg 7dCD 7FE9 7K3z W6mN 5FIh'))
$headers = @{ Authorization = "Basic $auth"; 'Content-Type' = 'application/json' }

$json = Get-Content 'e:\America Custom Boxes\acb_category_docs_extract.json' -Raw | ConvertFrom-Json

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
    $stopHeaders = @(
        'Industries Served','Applications','Available Box','Packaging Specification',
        'Specification','Our Manufacturing Process','Quality Assurance','FAQ',
        'Frequently Asked','Printing & Finishing Table','Add-ons','Insert Options',
        'Sustainable Packaging Options','Packaging Materials','Food Safety',
        'Bakery Packaging Guide','Candle Packaging Guide','Event Packaging Guide',
        'Mailer Packaging Guide','Tuck Packaging Guide','Pet Packaging Guide',
        'Popcorn Packaging Guide','Cosmetic Packaging Guide','Food Packaging Guide',
        'Product Packaging Guide','POD Packaging Guide','Pharmaceutical Packaging Guide'
    )

    $htmlParts = @()
    $mode = 'none'
    $whyItems = @()
    $benefitItems = @()

    foreach ($p in $paras) {
        if ($stopHeaders -contains $p) { break }
        if ($p -eq 'Introduction') { $mode = 'intro'; continue }
        if ($p -match '^Why Choose') { $mode = 'why'; $htmlParts += "<h3>$p</h3>"; continue }
        if ($p -eq 'Key Benefits') { $mode = 'benefits'; $htmlParts += "<h3>$p</h3>"; continue }
        if ($p -match '^(SEO Meta Title|Meta Description|URL Slug|Primary Keyword|Secondary Keywords|LSI Keywords|Long-Tail Keywords|Commercial Keywords|Transactional Keywords|Search Intent|Target Market|H1:|Hero Description|Get a Quote|THE VERTEX|SEO & On-Page|ACB CATEGORY|Custom Bakery Boxes|Custom Candle|Custom Event|Custom Mailer|Custom Product|Custom Tuck|Custom POD|Custom Pharmaceutical|Custom Pet|Custom Popcorn|Custom Cosmetic|Custom Food|Food-Grade|E-Commerce|Print-on-Demand|Premium Beauty|Retail-Ready|Event & Occasion|Packaging That|Packaging as|The Box Is|Launch Small|Ship-safe|Fresh, protected|Premium, retail|Give your|Not every|For an online|In beauty|Baked goods are|Event packaging|Popcorn is|Food brands|Pet parents|Pharmaceutical brands|Product boxes are|Tuck-end boxes|Mailer boxes are|Candle packaging|Small quantities|Retail brands need|Every brand deserves|When packaging|Your product deserves|Stand out|Make every|Turn every|Build brand|Protect your|Elevate your|Transform your|Upgrade your|Boost your|Enhance your|Improve your|Optimize your|Maximize your|Minimize your|Reduce your|Increase your|Expand your|Extend your|Develop your|Craft your|Create your|Design your|Print your|Ship your|Package your|Protect your|Preserve your|Maintain your|Sustain your|Support your|Ensure your|Deliver your|Provide your|Offer your|Supply your|Serve your|Help your|Work with|Partner with|Trust America|Choose America|Order custom|Request a quote|Get a quote|Free 3D|Free Die|No setup|No die|No plate|No minimum|Low MOQ|Fast turnaround|Free shipping|Free design|Free die|United States|All 50 states|Across the USA|Nationwide|USA-wide|US-wide|U\.S\.|United States — all 50 states)$') { continue }

        switch ($mode) {
            'intro' {
                if ($p.Length -gt 50) { $htmlParts += "<p>$p</p>" }
            }
            'why' {
                if ($p -match '^(.+?) [\u2014-] (.+)$') {
                    $whyItems += "<li><strong>$($Matches[1])</strong> - $($Matches[2])</li>"
                } elseif ($p -match '^(.+?) - (.+)$') {
                    $whyItems += "<li><strong>$($Matches[1])</strong> - $($Matches[2])</li>"
                } elseif ($p.Length -gt 30 -and $whyItems.Count -lt 8) {
                    $whyItems += "<li>$p</li>"
                }
            }
            'benefits' {
                if ($p -match '^(.+?) [\u2014-] (.+)$') {
                    $benefitItems += "<li><strong>$($Matches[1])</strong> - $($Matches[2])</li>"
                } elseif ($p -match '^(.+?) - (.+)$') {
                    $benefitItems += "<li><strong>$($Matches[1])</strong> - $($Matches[2])</li>"
                }
                if ($benefitItems.Count -ge 6) { break }
            }
        }
    }

    if ($whyItems.Count) { $htmlParts += "<ul>`n$($whyItems -join "`n")`n</ul>" }
    if ($benefitItems.Count) { $htmlParts += "<ul>`n$($benefitItems -join "`n")`n</ul>" }
    return ($htmlParts -join "`n")
}

$slugToId = @{
    'popcorn-boxes' = 38
    'bakery-boxes'  = 27
    'candle-boxes'  = 24
    'event-boxes'   = 40
    'mailer-boxes'  = 26
    'tuck-boxes'    = 39
    'pet-boxes'     = 33
}

$allBlocks = @{}
foreach ($prop in $json.PSObject.Properties) {
    $blocks = Get-CategoryBlocks $prop.Value
    foreach ($k in $blocks.Keys) {
        if (-not $allBlocks.ContainsKey($k)) { $allBlocks[$k] = $blocks[$k] }
    }
}

Write-Host "Parsed:" ($allBlocks.Keys -join ', ')

$results = @()
foreach ($slug in $slugToId.Keys) {
    if (-not $allBlocks.ContainsKey($slug)) {
        Write-Host "SKIP missing content: $slug"
        continue
    }
    $paras = $allBlocks[$slug]
    $meta = Parse-Meta $paras
    $html = Build-ArchiveHtml $paras
    $id = $slugToId[$slug]

    # Update description via WC API
    $wcBody = @{ description = $html } | ConvertTo-Json -Depth 3
    Invoke-RestMethod -Method PUT -Uri "https://americacustomboxes.com/wp-json/wc/v3/products/categories/$id" -Headers $headers -Body $wcBody | Out-Null

    # Update Yoast meta via WP REST
    $wpBody = @{
        meta = @{
            wpseo_title    = $meta.title
            wpseo_metadesc = $meta.description
            wpseo_focuskw  = $meta.focuskw
        }
    } | ConvertTo-Json -Depth 5
    Invoke-RestMethod -Method POST -Uri "https://americacustomboxes.com/wp-json/wp/v2/product_cat/$id" -Headers $headers -Body $wpBody | Out-Null

    Write-Host "OK $slug ($id) - $($meta.title)"
    $results += [PSCustomObject]@{ slug = $slug; id = $id; title = $meta.title; focuskw = $meta.focuskw; htmlLen = $html.Length }
}

$results | ConvertTo-Json | Set-Content 'e:\America Custom Boxes\deploy_results.json' -Encoding utf8
$results | Format-Table -AutoSize
