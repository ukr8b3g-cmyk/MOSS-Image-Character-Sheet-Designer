# Changelog

## v1.0.1

- Add the Prompts tab with 13 editable MOSS base instructions, Apply, per-view Reset and settings preview in English/Japanese.
- Save optional per-view overrides with workflows, including explicit empty strings; restore on reload and validate the 2,000 UTF-16-unit limit.
- Preserve edits through feature extraction, including empty outfit facts, in both Layout JSON and Caption output.
- Keep unedited defaults, existing workflows, node identifiers/display names, sockets and model/sampling settings unchanged. Display names retain v1.0; package metadata is 1.0.1.
- Python24 / JavaScript DOM9 pass; local Chrome persistence and live preview API checked. Feature preservation uses controlled feature JSON. No new encoder/GPU quality benchmark; garment fragments, repeated/missing views and image-to-text information loss remain possible.

## v1.0

- Keep one user-facing Text or Image workflow in examples and attach it to this Release.
- Keep runtime defaults in contracts/default_state.json and move the five required regression fixtures into tests/fixtures; remove unused example data and obsolete local templates.
- Explain text input and image-to-description-to-T2I generation prominently in both READMEs, with current model filenames and download URLs. Preserve the user-added README images.
- Align package, node display and UI version labels to 1.0. Node identifiers, sockets, generation logic and workflow settings remain unchanged.
- Retain the v0.2.1 fixes and visual limitations below. Internal prompt compiler remains moss-sheet-1.4.1.

## v0.2.1

- Preserve explicit garment part prompts and clothing shape when extracted outfit facts are empty, including clothing-only sheets.
- Use actual computed layouts for all-13 summaries and retain per-panel positions in Caption output through shared serialization.
- Reject invalid Unicode and external prompts over 2,000 UTF-16 units before feature analysis, reporting the prompt input.
- Align Footwear off with preserving described socks/tights; correct Settings documentation.
- Add six targeted regressions: Python21 and DOM8 pass, 10 existing preset/input results remain identical. Two GPU smoke images saved successfully.
- Known limits remain: garment head/body fragments, extra heads and repeated viewpoints. Empty-string model-output frequency and a new multi-seed quality benchmark were not measured.

Internal prompt compiler: moss-sheet-1.4.1. UI, sockets and workflow node names are unchanged.

## v0.2.0

- Initial public release: MOSS-specific character-sheet designer and text/image subgraph workflow.
- Illustrated 13-view selection, compact controls, grouped Auto layout, part prompts, styles and saved state.
- Existing MOSS encoder reuse for selected head/clothing descriptions; working simpler presets retain their existing path.
- Garments-only clothing instructions, without Worn mode or an extra visible CLIP socket.
- English/Japanese setup and usage, model URLs, image-to-description regeneration explanation and explicit visual limitations.

Package version v0.2.0 and internal prompt compiler revision moss-sheet-1.4.0 are separate identifiers.
