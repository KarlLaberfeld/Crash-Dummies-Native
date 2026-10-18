param([switch]$IncludeLocalAssets)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$executable = Join-Path $PSScriptRoot 'build/CrashDummiesNative.exe'
if (-not (Test-Path -LiteralPath $executable -PathType Leaf)) { throw 'Build the Windows executable first with build.ps1.' }
& python tools/build_manifest.py verify
if ($LASTEXITCODE -ne 0) { throw 'Package refused: rebuild from the clean committed source.' }
$buildInfo = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'build/build-info.json') -Raw | ConvertFrom-Json
$revision = $buildInfo.sourceRevision
$sourceDirty = $false
$version = $buildInfo.version
$identity = 'CrashDummiesNative-' + $version + '-windows-x64-' + [guid]::NewGuid().ToString('N').Substring(0,8)
$distribution = Join-Path $PSScriptRoot 'dist'
$packageRoot = Join-Path $distribution $identity
New-Item -ItemType Directory -Path $packageRoot -Force | Out-Null
Copy-Item -LiteralPath $executable -Destination $packageRoot
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'build/build-info.json') -Destination $packageRoot
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'docs/RELEASE_NOTES.md') -Destination $packageRoot
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'docs/PROVENANCE.md') -Destination $packageRoot
$assets = @('crash.dat','air.dat','ski.dat','bomb.dat','cruise.dat','ui.dat','audio.dat')
if ($IncludeLocalAssets) {
    foreach ($name in $assets) {
        $source = Join-Path (Join-Path $PSScriptRoot 'build') $name
        if (-not (Test-Path -LiteralPath $source -PathType Leaf)) { throw "Missing local asset: $name" }
        Copy-Item -LiteralPath $source -Destination $packageRoot
    }
} else {
    $toolDirectory = Join-Path $packageRoot 'tools'
    New-Item -ItemType Directory -Path $toolDirectory | Out-Null
    foreach ($name in @('extract.py','extract_air.py','extract_ski.py','extract_bomb.py','extract_cruise.py','extract_ui.py','extract_audio.py','analyze_audio.py')) {
        Copy-Item -LiteralPath (Join-Path (Join-Path $PSScriptRoot 'tools') $name) -Destination $toolDirectory
    }
    @'
param([Parameter(Mandatory=$true)][string]$Rom)
$ErrorActionPreference = 'Stop'
$cartridge = (Resolve-Path -LiteralPath $Rom).Path
foreach ($tool in @('extract','extract_air','extract_ski','extract_bomb','extract_cruise','extract_ui','extract_audio')) {
    & python (Join-Path $PSScriptRoot "tools/$tool.py") $cartridge --out $PSScriptRoot
    if ($LASTEXITCODE -ne 0) { throw "Asset extraction failed: $tool" }
}
Write-Output 'Local assets prepared. Start CrashDummiesNative.exe.'
'@ | Set-Content -LiteralPath (Join-Path $packageRoot 'Prepare-Assets.ps1') -Encoding UTF8
}
$assetNotice = if ($IncludeLocalAssets) { 'LOCAL USE ONLY: this package contains extracted original game data. Do not upload it.' } else { 'This package contains no original game data. Run Prepare-Assets.ps1 -Rom <path-to-your-ROM> with Python 3.10+ before launching.' }
@"
Crash Dummies Native - Windows alpha
Version: $version
Source revision: $revision

This is an unfinished development build, not a final release.
$assetNotice

Extract the complete folder, then run CrashDummiesNative.exe on Windows x64.
Python is needed only for preparing assets, not for running the game.
No Game Boy CPU emulator is used. Keep all seven .dat files next to the EXE.

Enter: start/continue/pause. Tab: options. Arrow keys: movement/selection.
Z/X: A/B actions. Escape: pause. F6: abandon campaign and return to title.
High scores: arrows choose a character; Z/X confirm; select End to finish.
Scores are retained only for the current application session.
Xbox-compatible XInput controller: D-pad/left stick = directions, A/B = actions,
Start = start/continue/pause, Back/View = Select/options. Release controls after
connecting or returning focus. Disconnect pauses gameplay. One pad is used for
both alternating players. DirectInput-only devices and remapping are unsupported.

Air Bumper retains delayed crash-recovery requests to prevent a reproduced
stall. This is a documented native stability correction; exact original
timing, image and audio equivalence remain unverified. Automated
completion tests do not replace original-reference or human play tests.
The Windows application shell is in English. See the repository status for
the current evidence and remaining work.

Private project: https://github.com/KarlLaberfeld/Crash-Dummies-Native
"@ | Set-Content -LiteralPath (Join-Path $packageRoot 'README.txt') -Encoding UTF8
$hashes = @(Get-ChildItem -LiteralPath $packageRoot -File -Recurse | Sort-Object FullName | ForEach-Object {
    @{ path=$_.FullName.Substring($packageRoot.Length+1).Replace('\','/'); sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant() }
})
@{ preview=$true; version=$version; sourceRevision=$revision; sourceDirty=$sourceDirty; containsOriginalData=[bool]$IncludeLocalAssets; files=$hashes } |
    ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $packageRoot 'manifest.json') -Encoding UTF8
$archive = Join-Path $distribution ($identity + '.zip')
Compress-Archive -LiteralPath $packageRoot -DestinationPath $archive
if (-not $IncludeLocalAssets) {
    & python tools/verify_package.py $archive
    if ($LASTEXITCODE -ne 0) { throw 'ROM-free package verification failed.' }
}
Write-Output "Preview folder: $packageRoot"
Write-Output "Preview archive: $archive"
