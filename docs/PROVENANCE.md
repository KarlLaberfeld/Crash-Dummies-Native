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

## MIT license scope

The project's own contributions are offered under the MIT License in `LICENSE`,
to the extent the contributors hold the necessary rights. The standard MIT text
is unmodified. Its permissions, including commercial use and redistribution,
are not restricted by this repository currently being private.

The grant does not include the original ROM, extracted graphics/music/game data,
trademarks or third-party rights that contributors do not hold. Reconstructing
or translating the original game may involve protected expression; placing MIT
in this repository does not settle that issue or establish clean-room provenance.
Original rights holders retain their rights. Any broader distribution still
requires appropriate review of the reconstructed material and its provenance.
