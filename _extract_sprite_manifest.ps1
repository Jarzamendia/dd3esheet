$src = Get-Content -Raw -Encoding UTF8 -LiteralPath 'design_handoff_dnd_vtt\data\assets.js'
$start = $src.IndexOf('{')
$end = $src.LastIndexOf('}')
$obj = $src.Substring($start, $end - $start + 1)
$data = $obj | ConvertFrom-Json
New-Item -ItemType Directory -Force -Path 'dd3esheet\sprites\fixtures' | Out-Null
$data | ConvertTo-Json -Depth 20 | Set-Content -Encoding UTF8 -LiteralPath 'dd3esheet\sprites\fixtures\sprite_manifest.json'
Write-Output "assets: $($data.total) sections: $($data.sections.Count)"
