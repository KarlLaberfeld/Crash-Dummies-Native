# Crash Dummies Native 0.1.0-alpha.1

Experimental Windows x64 pre-release. This is not a final or fully faithful port.

## Installation

Extract the complete ZIP. With Python 3.10+ available, run
`./Prepare-Assets.ps1 -Rom 'path/to/your/original.gb'` once, then launch
`CrashDummiesNative.exe`. The US/Europe ROM revision and SHA-256 are specified
in the repository README: 131072 bytes, SHA-256
`ef563c4a4b063ea045d71b435dd078c19d0738f85079928803167cee8f34a4ec`.
No ROM, extracted game assets or reference recordings
are included. Python is not required while playing.

## Included

All five reconstructed stunts and four difficulties, campaign/two-player turns,
original menus/results/ending, native music/effects, keyboard input and
Xbox-compatible XInput controller input. D-pad/left stick moves, A/B act,
Start/Menu starts or pauses, Back/View selects/options. Release controls after
connecting or regaining focus. One pad is shared by alternating players.

## Known limitations

- The production Windows scheduler does not yet use the experimental original
  timing model. Diagnostic timing matches must not be read as EXE-wide parity.
- Full original image, audio and behavior comparisons remain incomplete.
- Air crash recovery deliberately fixes a stall also observed in the original.
- High scores are session-only. No save states, campaign resume, remapping,
  fullscreen, volume menu or persistent settings.
- DirectInput-only controllers and vibration are unsupported.
- Physical controller use, physical audio removal, human campaign acceptance
  and an independent Windows installation remain unverified.
- The reconstructed code's licensing/provenance review remains open; this
  pre-release stays in the private repository.

## Validation

Release package verification is recorded in the accompanying validation report.
Automated controller samples verify the input pipeline; they are not physical
controller qualification. No final-release status is claimed.
