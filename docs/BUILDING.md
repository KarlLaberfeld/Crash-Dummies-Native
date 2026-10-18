# Building Crash Dummies Native

Use Windows x64, Python 3.10+ and Zig 0.16.0. Put Python/Git/Zig on PATH, or
pass the compiler location with `-Compiler`. No Python packages are required.

```powershell
./build.ps1 -Rom 'C:\path\to\original.gb' -Test
```

Exactly one `.gb` file in the project directory is detected automatically.
Only the US/Europe revision and hash in the README are accepted. `-SkipExtract`
reuses already prepared local assets. Generated data remains under ignored
`build/`. The executable is `build/CrashDummiesNative.exe`.

Additional host integration tests:

```powershell
./build/CrashDummiesNative.exe --ui-smoke-test
./build/CrashDummiesNative.exe --ui-no-audio-test
./build/CrashDummiesNative.exe --controller-smoke-test
./build/CrashDummiesNative.exe --audio-smoke-test
```

Tests write local logs beside the executable (native self-tests use the working
directory). The controller window test injects controller samples into the same
mapping/focus/edge pipeline used by XInput; it does not simulate a physical USB
device or certify hardware. Native pilots complete all stunts and campaigns
using button inputs, not injected success results. They do not prove fidelity.

## Packaging

Commit changes, rebuild, then run `./package.ps1`. Packaging checks a build-time
manifest against the current source revision, all C++ inputs and the EXE hash;
dirty/stale builds are rejected. The ignored `dist/` ZIP contains only the EXE,
asset preparation scripts, notices and manifests. Verify the ZIP itself, extract
it to a fresh folder with spaces, prepare assets there, and run its tests from
a different working directory before attaching it to a release.

`./package.ps1 -IncludeLocalAssets` is only for local copies and must never be
uploaded. Original data, screenshots, music captures and independent SameBoy
reference measurements stay local. The reference backend is not linked into
the game or included in its release.

Historical documents name `CrashDummies.exe`, the executable name before the
Crash Dummies Native alpha. Those names/hashes identify their original tests.
