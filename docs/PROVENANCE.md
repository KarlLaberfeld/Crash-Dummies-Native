# Provenance and licensing status

Crash Dummies Native is an unofficial native C++/Win32 reconstruction of the
Game Boy release of The Incredible Crash Dummies. It is not affiliated with
the original developers, publishers or rights holders.

- Game behavior was reconstructed through static ROM inspection and separate
  original-reference measurements. Source addresses and evidence limits are
  documented throughout `docs/`. This is not a claim of clean-room development.
- Original graphics, maps, animation/music data and other game assets are read
  from a user-supplied, hash-checked ROM by the offline extraction tools. Neither
  the ROM nor the extracted files are included in source or release packages.
- The native Windows application contains no Game Boy CPU emulator. Separate
  SameBoy measurements use a pinned local backend, excluded from the game,
  distribution and repository. See `REFERENCE_BACKENDS.md` for its provenance.
- Win32/GDI/waveOut and XInput are Windows system APIs. XInput is loaded from
  the system directory; no Microsoft controller DLL is bundled. Zig is the build
  toolchain, Python is used for extraction/testing; neither is bundled.
- Development has used AI assistance. This does not establish copyright
  ownership or grant rights to original game code, expression or assets.

No blanket open-source license has been assigned to the reconstructed game code.
The alpha is distributed within the existing private repository for evaluation.
Do not infer permission to redistribute original material from the repository's
availability, the absence of a ROM, or an unofficial-project disclaimer.
Any future public distribution or license grant needs an appropriate provenance
and rights review. Original game content and trademarks remain with their
respective rights holders.
