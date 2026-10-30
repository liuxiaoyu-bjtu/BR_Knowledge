$ErrorActionPreference = 'Stop'
$project = Join-Path (Get-Location) '05-internal-materials/vocational-planning/03_X课程项目'
$destination = Join-Path (Get-Location) '99-task-contexts/20261030-全课评价补齐与U4P3/qa-render'
New-Item -ItemType Directory -Path $destination -Force | Out-Null
$codes = @('U4-L1', 'U5-L1', 'U5-L2', 'U5-L3')
$issues = @()
$app = New-Object -ComObject PowerPoint.Application
try {
    foreach ($code in $codes) {
        $deck = Get-ChildItem -LiteralPath (Join-Path $project 'PPT') -Filter ($code + '*_Codex审查版.pptx') | Select-Object -First 1
        $pres = $app.Presentations.Open($deck.FullName, $true, $false, $false)
        try {
            $target = Join-Path $destination $code
            New-Item -ItemType Directory -Path $target -Force | Out-Null
            foreach ($slide in $pres.Slides) {
                $slide.Export((Join-Path $target ('slide-{0:D2}.png' -f $slide.SlideIndex)), 'PNG', 1600, 900)
                foreach ($shape in $slide.Shapes) {
                    if ($shape.HasTextFrame -and $shape.TextFrame.HasText) {
                        $r = $shape.TextFrame2.TextRange
                        $bottom = $r.BoundTop + $r.BoundHeight - $shape.Top - $shape.Height
                        $right = $r.BoundLeft + $r.BoundWidth - $shape.Left - $shape.Width
                        if ($bottom -gt 3 -or $right -gt 3) {
                            $issues += [PSCustomObject]@{deck=$code; page=$slide.SlideIndex; shape=$shape.Id; bottom=[Math]::Round($bottom,1); right=[Math]::Round($right,1); text=$shape.TextFrame.TextRange.Text}
                        }
                    }
                }
            }
            Write-Output ($code + ': ' + $pres.Slides.Count + ' slides exported')
        } finally { $pres.Close() }
    }
} finally { $app.Quit() }
ConvertTo-Json -InputObject @($issues) -Depth 4 | Set-Content -LiteralPath (Join-Path $destination 'bounds.json') -Encoding UTF8
Write-Output ('Bounds findings: ' + $issues.Count)
