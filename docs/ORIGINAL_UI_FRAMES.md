# Stable original UI framebuffer comparisons

October 20, 2026. Twenty-eight complete 160x144 frames now match the original
pixel for pixel: four fully revealed Air instruction pictures, four complete
scrolled instructions with the Start prompt, and twenty title pictures covering
the five-page carousel after A/B in both retained histories. All 645,120 logical
grayscale pixels match. No crop, tolerance, palette fitting or image replacement
is used.

Original images come directly from the pinned SameBoy framebuffer. The adapter
uses its fixed four-shade grayscale palette. Captures read existing accepted
input-only controls and preserve the complete observed/unobserved end-state
hash. Instruction pictures are sampled at the accepted incoming-fade endpoint.
Prompt pictures are sampled after the second completed input wait, when text
and prompt are stable. Title pages use the second idle wait after reopening;
page zero is observed after the completed carousel wrap and two further waits.
Their clocks, callback geometry and complete ancestor comparisons are checked.

Native images are produced by the production `UiFlow::render` function, using
decoded local assets and independently computed native state. The instruction
map includes the native header, picture, text and prompt stores; the scroll value
comes from the native text owner. The title renderer uses native page selection
and retained initial scores. No original image, map or observed clock enters
the native renderer. Both images normalize to the same four logical shades;
every pixel, including image edges, is compared.

Use `tools/ui_frame_reference.py capture ROM --kind instruction|title --capture
CONTROL --parent ACCEPTED_JSON --out FRAME_FOLDER`. Instruction parents are
full-prompt `selected_text_reference` recordings; title parents are complete
`title_cycle_reference` recordings. Build/run the native diagnostic with
`--players-gameplay` or `--title-cycle` to emit `.frame.shades` files from native
owners. `compare` takes the same paths and `--qualification ARGUMENTS_JSON`,
containing the appropriate full parent-comparator arguments. The Python
`compare_many` API qualifies shared parent chains once per family and audits
each frame's own parent/file hashes and complete pixel count.

All original PNGs, shade buffers, ROM/assets and native frame outputs remain
local. Git contains only observation/comparison code, synthetic integrity tests
and this result summary. Thirty-one focused tests reject truncated images,
wrong dimensions/modes/shades/themes, detached frame owners, wrong sampling
boundaries and incomplete page sets; one-pixel changes are reported exactly.

This qualifies stable content in the production renderer. It does not qualify
transition frames, LCD scanline timing in the Windows scheduler, host window
scaling/color themes, gameplay frames, other players/stunts/difficulties, PCM
audio or physical hardware. See the [comparison matrix](ORIGINAL_COMPARISON_SCOPE.md)
and [final acceptance](ACCEPTANCE.md); the broader work remains incomplete.
