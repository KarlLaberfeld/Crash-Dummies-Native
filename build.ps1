param([string]$Rom, [string]$Compiler, [switch]$SkipExtract, [switch]$Test)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not $Compiler) {
    $bundled = Join-Path $PSScriptRoot '.tools\zig-x86_64-windows-0.16.0\zig.exe'
    if (Test-Path -LiteralPath $bundled) { $Compiler = $bundled }
    elseif (Get-Command zig -ErrorAction SilentlyContinue) { $Compiler = (Get-Command zig).Source }
    else { throw 'Zig was not found. Install Zig 0.16.0 or pass its path with -Compiler.' }
}
New-Item -ItemType Directory -Force -Path build | Out-Null
$env:ZIG_GLOBAL_CACHE_DIR = Join-Path $PSScriptRoot '.tools\zig-cache'
$env:ZIG_LOCAL_CACHE_DIR = Join-Path $PSScriptRoot '.tools\zig-local-cache'
if (-not $SkipExtract) {
    if (-not $Rom) {
        $files = @(Get-ChildItem -LiteralPath $PSScriptRoot -Filter '*.gb' -File)
        if ($files.Count -ne 1) { throw 'Place exactly one original ROM in this directory or specify -Rom.' }
        $Rom = $files[0].FullName
    }
    & python tools/extract.py $Rom --out build
    if ($LASTEXITCODE -ne 0) { throw 'Extraction failed.' }
    & python tools/extract_air.py $Rom --out build
    if ($LASTEXITCODE -ne 0) { throw 'Air Bumper extraction failed.' }
    & python tools/extract_ski.py $Rom --out build
    if ($LASTEXITCODE -ne 0) { throw 'Ski Slope extraction failed.' }
    & python tools/extract_bomb.py $Rom --out build
    if ($LASTEXITCODE -ne 0) { throw 'Bomb Factory extraction failed.' }
    & python tools/extract_cruise.py $Rom --out build
    if ($LASTEXITCODE -ne 0) { throw 'Cruise Missile extraction failed.' }
    & python tools/extract_ui.py $Rom --out build
    if ($LASTEXITCODE -ne 0) { throw 'UI extraction failed.' }
}
& $Compiler c++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -Wno-nullability-completeness -Wno-unused-command-line-argument -Isrc src/main.cpp src/game.cpp src/air.cpp src/ski.cpp src/bomb.cpp src/cruise.cpp src/ui.cpp tests/native_tests.cpp tests/air_tests.cpp tests/ski_tests.cpp tests/bomb_tests.cpp tests/cruise_tests.cpp tests/campaign_tests.cpp tests/ui_tests.cpp -o build/CrashDummies.exe -target x86_64-windows-gnu -municode '-Wl,--subsystem,windows' -luser32 -lgdi32 -lshell32
if ($LASTEXITCODE -ne 0) { throw 'Compilation failed.' }
if ($Test) {
    & python -m unittest discover -s tests -p 'test_*.py'
    if ($LASTEXITCODE -ne 0) { throw 'Extractor tests failed.' }
    Push-Location build
    try {
        $process = Start-Process -FilePath '.\CrashDummies.exe' -ArgumentList '--self-test' -Wait -PassThru -WindowStyle Hidden
        Get-Content self-test.txt
        Get-Content air-test.txt
        Get-Content ski-test.txt
        Get-Content bomb-test.txt
        Get-Content cruise-test.txt
        Get-Content campaign-test.txt
        Get-Content ui-test.txt
        if ($process.ExitCode -ne 0) { throw 'Native tests failed.' }
    } finally { Pop-Location }
}
Write-Output 'Built: build\CrashDummies.exe (development build, not the complete game)'
