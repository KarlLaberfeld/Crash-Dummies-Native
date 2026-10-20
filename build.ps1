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
    & python tools/extract_audio.py $Rom --out build
    if ($LASTEXITCODE -ne 0) { throw 'Audio extraction failed.' }
    & python tools/extract_ui.py $Rom --out build
    if ($LASTEXITCODE -ne 0) { throw 'UI extraction failed.' }
}
& python tools/build_manifest.py begin
if ($LASTEXITCODE -ne 0) { throw 'Build identity preparation failed.' }
& $Compiler c++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -Wno-nullability-completeness -Wno-unused-command-line-argument -Isrc src/main.cpp src/game.cpp src/air.cpp src/ski.cpp src/bomb.cpp src/cruise.cpp src/ui.cpp src/audio.cpp tests/native_tests.cpp tests/air_tests.cpp tests/ski_tests.cpp tests/bomb_tests.cpp tests/cruise_tests.cpp tests/campaign_tests.cpp tests/ui_tests.cpp tests/playthrough_tests.cpp tests/audio_tests.cpp tests/sprite_tests.cpp -o build/CrashDummiesNative.exe -target x86_64-windows-gnu -municode '-Wl,--subsystem,windows' -luser32 -lgdi32 -lshell32 -lwinmm
if ($LASTEXITCODE -ne 0) { throw 'Compilation failed.' }
& python tools/build_manifest.py finish
if ($LASTEXITCODE -ne 0) { throw 'Build identity verification failed.' }
if ($Test) {
    & $Compiler c++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -Isrc tests/controller_tests.cpp -o build/controller-tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Controller test compilation failed.' }
    & ./build/controller-tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Controller tests failed.' }
    & $Compiler c++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -Isrc tests/air_work_tests.cpp src/air.cpp src/game.cpp -o build/air-work-tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Air source-work test compilation failed.' }
    & ./build/air-work-tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Air source-work tests failed.' }
    & $Compiler c++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -Isrc tests/air_pause_clock_tests.cpp -o build/air-pause-clock-tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Air pause access test compilation failed.' }
    & ./build/air-pause-clock-tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Air pause access tests failed.' }
    & $Compiler c++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -Isrc tests/air_result_clock_tests.cpp src/audio.cpp -o build/air-result-clock-tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Air result-clock test compilation failed.' }
    & ./build/air-result-clock-tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Air result-clock tests failed.' }
    & $Compiler c++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -Isrc tests/air_final_result_tests.cpp src/audio.cpp -o build/air-final-result-tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Air final-result test compilation failed.' }
    & ./build/air-final-result-tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Air final-result tests failed.' }
    & $Compiler c++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -Isrc tests/air_title_reset_tests.cpp src/audio.cpp -o build/air-title-reset-tests.exe
    if ($LASTEXITCODE -ne 0) { throw "Title reset test compilation failed" }
    & ./build/air-title-reset-tests.exe
    if ($LASTEXITCODE -ne 0) { throw "Title reset tests failed" }
    & $Compiler c++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -Isrc tests/air_title_layout_tests.cpp src/audio.cpp -o build/air-title-layout-tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Title layout test compilation failed.' }
    & ./build/air-title-layout-tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Title layout tests failed.' }
    & $Compiler c++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -Isrc tests/air_title_fade_tests.cpp src/audio.cpp -o build/air-title-fade-tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Title fade test compilation failed.' }
    & ./build/air-title-fade-tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Title fade tests failed.' }
    & $Compiler c++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -Isrc tests/air_title_close_tests.cpp src/audio.cpp -o build/air-title-close-tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Title closing test compilation failed.' }
    & ./build/air-title-close-tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Title closing tests failed.' }
    & $Compiler c++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -Isrc tests/air_title_page_tests.cpp src/audio.cpp -o build/air-title-page-tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Title page test compilation failed.' }
    & ./build/air-title-page-tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Title page tests failed.' }
    & $Compiler c++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -Isrc tests/air_title_menu_tests.cpp src/audio.cpp -o build/air-title-menu-tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Title menu test compilation failed.' }
    & ./build/air-title-menu-tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Title menu tests failed.' }
    & $Compiler c++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -Isrc tests/air_title_start_tests.cpp src/audio.cpp -o build/air-title-start-tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Title Start test compilation failed.' }
    & ./build/air-title-start-tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Title Start tests failed.' }
    & $Compiler c++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -Isrc tests/air_title_campaign_tests.cpp src/audio.cpp -o build/air-title-campaign-tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Title campaign test compilation failed.' }
    & ./build/air-title-campaign-tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Title campaign tests failed.' }
    & $Compiler c++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -Isrc tests/air_title_resume_tests.cpp src/audio.cpp -o build/air-title-resume-tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Title resume test compilation failed.' }
    & ./build/air-title-resume-tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Title resume tests failed.' }
    & $Compiler c++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -Isrc tests/air_title_header_tests.cpp src/audio.cpp -o build/air-title-header-tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Title header test compilation failed.' }
    & ./build/air-title-header-tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Title header tests failed.' }
    & $Compiler c++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -Isrc tests/air_title_picture_tests.cpp src/audio.cpp -o build/air-title-picture-tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Title picture test compilation failed.' }
    & ./build/air-title-picture-tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Title picture tests failed.' }
    & $Compiler c++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -Isrc tests/air_title_unlock_tests.cpp src/audio.cpp -o build/air-title-unlock-tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Title unlock test compilation failed.' }
    & ./build/air-title-unlock-tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Title unlock tests failed.' }
    & python -m unittest discover -s tests -p 'test_*.py'
    if ($LASTEXITCODE -ne 0) { throw 'Extractor tests failed.' }
    Push-Location build
    try {
        $process = Start-Process -FilePath '.\CrashDummiesNative.exe' -ArgumentList '--self-test' -Wait -PassThru -WindowStyle Hidden
        Get-Content self-test.txt
        Get-Content air-test.txt
        Get-Content ski-test.txt
        Get-Content bomb-test.txt
        Get-Content cruise-test.txt
        Get-Content campaign-test.txt
        Get-Content ui-test.txt
        Get-Content playthrough-test.txt
        Get-Content audio-test.txt
        Get-Content sprite-test.txt
        if ($process.ExitCode -ne 0) { throw 'Native tests failed.' }
    } finally { Pop-Location }
}
Write-Output 'Built: build\CrashDummiesNative.exe (development build, not the complete game)'
