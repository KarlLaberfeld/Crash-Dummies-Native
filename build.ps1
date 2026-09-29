param([string]$Rom, [string]$Compiler, [switch]$SkipExtract, [switch]$Test)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not $Compiler) {
    $bundled = Join-Path $PSScriptRoot '.tools\zig-x86_64-windows-0.16.0\zig.exe'
    if (Test-Path -LiteralPath $bundled) { $Compiler = $bundled }
    elseif (Get-Command zig -ErrorAction SilentlyContinue) { $Compiler = (Get-Command zig).Source }
    else { throw 'Zig fehlt. Installiere Zig 0.16.0 oder gib -Compiler mit dem Pfad zu zig.exe an.' }
}
New-Item -ItemType Directory -Force -Path build | Out-Null
$env:ZIG_GLOBAL_CACHE_DIR = Join-Path $PSScriptRoot '.tools\zig-cache'
$env:ZIG_LOCAL_CACHE_DIR = Join-Path $PSScriptRoot '.tools\zig-local-cache'
if (-not $SkipExtract) {
    if (-not $Rom) {
        $files = @(Get-ChildItem -LiteralPath $PSScriptRoot -Filter '*.gb' -File)
        if ($files.Count -ne 1) { throw 'Bitte genau eine Original-ROM ablegen oder -Rom angeben.' }
        $Rom = $files[0].FullName
    }
    & python tools/extract.py $Rom --out build
    if ($LASTEXITCODE -ne 0) { throw 'Extraktion fehlgeschlagen.' }
}
& $Compiler c++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -Wno-nullability-completeness -Wno-unused-command-line-argument -Isrc src/main.cpp src/game.cpp tests/native_tests.cpp -o build/CrashDummies.exe -target x86_64-windows-gnu -municode -mwindows -luser32 -lgdi32 -lshell32
if ($LASTEXITCODE -ne 0) { throw 'Kompilierung fehlgeschlagen.' }
if ($Test) {
    & python -m unittest discover -s tests -p 'test_*.py'
    if ($LASTEXITCODE -ne 0) { throw 'Extraktortests fehlgeschlagen.' }
    Push-Location build
    try {
        $process = Start-Process -FilePath '.\CrashDummies.exe' -ArgumentList '--self-test' -Wait -PassThru -WindowStyle Hidden
        Get-Content self-test.txt
        if ($process.ExitCode -ne 0) { throw 'Native Tests fehlgeschlagen.' }
    } finally { Pop-Location }
}
Write-Output 'Erstellt: build\CrashDummies.exe (Entwicklungsstand, keine fertige Vollversion)'
