$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$source = Join-Path $root '트럼프_Truth_Social_Korea_Steel_분석보고서.md'
$target = Join-Path $root 'index.html'
$markdown = Get-Content -LiteralPath $source -Raw
$body = (ConvertFrom-Markdown -InputObject $markdown).Html

$html = @"
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>트럼프 Truth Social의 Korea·Steel 게시물 분석</title>
  <style>
    :root { color-scheme: light; }
    body { margin: 0; color: #1f2937; background: #f8fafc; font-family: system-ui, -apple-system, "Segoe UI", sans-serif; line-height: 1.7; }
    main { max-width: 960px; margin: 0 auto; padding: 48px 28px 80px; background: #fff; box-shadow: 0 0 32px rgba(15, 23, 42, .07); }
    h1, h2, h3 { color: #0f172a; line-height: 1.3; }
    h1 { border-bottom: 3px solid #b91c1c; padding-bottom: 16px; }
    h2 { margin-top: 44px; border-bottom: 1px solid #cbd5e1; padding-bottom: 8px; }
    a { color: #1d4ed8; }
    .downloads { display: flex; flex-wrap: wrap; gap: 12px; margin: 0 0 32px; padding: 18px 0 26px; border-bottom: 1px solid #cbd5e1; }
    .download { display: inline-block; padding: 10px 16px; border-radius: 8px; background: #10233f; color: #fff; font-weight: 700; text-decoration: none; }
    .download.secondary { background: #a5292a; }
    table { display: block; width: 100%; overflow-x: auto; border-collapse: collapse; }
    th, td { padding: 10px 12px; border: 1px solid #cbd5e1; vertical-align: top; }
    th { background: #f1f5f9; }
    blockquote { margin-left: 0; padding-left: 18px; border-left: 4px solid #94a3b8; color: #475569; }
    code { background: #f1f5f9; padding: 2px 5px; border-radius: 4px; }
    @media (max-width: 700px) { main { padding: 28px 18px 60px; } }
  </style>
</head>
<body>
  <main>
    <nav class="downloads" aria-label="보고서 다운로드">
      <a class="download" href="downloads/trump-korea-steel-report.md" download>MD 다운로드</a>
      <a class="download secondary" href="downloads/trump-korea-steel-report.pptx" download>PPT 다운로드</a>
    </nav>
$body
  </main>
</body>
</html>
"@

[IO.File]::WriteAllText($target, $html, [Text.UTF8Encoding]::new($false))
