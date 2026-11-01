# Validation and limits

Tested locally with ComfyUI 0.43.0, frontend 1.57.4 and Python 3.12.12.

- Python: 21 tests for state, layout fixtures, dimensions, input contracts and feature compilation, including six regression tests added after the v0.2.0 audit.
- DOM: 8 tests for controls, persistence and restoration.
- Five unaffected presets under two inputs retained identical compiled prompts and dimensions in local regression comparisons.
- Local GPU comparisons exercised clothing, head and all-13 selections across different subjects/seeds, plus text/image workflows using the existing encoder.

The v0.2.1 (moss-sheet-1.4.1) correction preserves explicit garment details when extracted outfit facts are empty, derives all-13 summaries from the computed layout, retains per-panel positions in caption output, and rejects prompts over 2,000 UTF-16 code units before analysis. Footwear off preserves described socks/tights. Settings provides saved JSON recovery, not the final runtime prompt. Two targeted GPU smoke runs saved images and confirmed the corrected runtime prompt structure. The empty-string outfit branch uses controlled CPU test data; the real extractor returned literal None text, so empty-string frequency is unmeasured. The garment smoke retained head/body fragments and the vertical Manual all-13 Caption image had extra heads and repeated directions.

These checks do not imply perfect viewpoint or visual compliance. Remaining failures include repeated directions, extra/missing heads, cropped hair and body fragments in garment panels. Physical Windows IME and Nodes 2.0 acceptance are unverified.

From the repository root:

```sh
python -m unittest discover -s tests -v
```

For DOM tests, supply an existing jsdom module directory through MOSS_TEST_JSDOM, then:

```sh
node --test tests/ui.test.js
```

Test-only packages are not required for normal ComfyUI use. Fixtures in examples/ and verification/layout_golden_cases.json support the suites. The recommended user workflow is the Text or Image template.
