# MOSS-Image Character Sheet Designer

[日本語](README.ja.md) · [Workflow](examples/MOSS-Image%20Character%20Sheet%20Designer%20-%20Text%20or%20Image.json) · [Releases](https://github.com/ukr8b3g-cmyk/MOSS-Image-Character-Sheet-Designer/releases)

A visual character-sheet layout node for ComfyUI and MOSS-Image. Select illustrated views and generate from text or an image described by the existing MOSS text encoder. The compact interface follows the H3 Reference13 designer, with MOSS-specific prompt compilation.

**Image input is image → text description → new image generation.** It is not direct image editing or pixel-based reference conditioning. The encoder describes the input, then MOSS generates a new sheet. Identity, clothing details, colors, lettering and unseen views can differ. Use an image-editing model when exact preservation matters.

## Installation

1. Use a recent [ComfyUI](https://github.com/Comfy-Org/ComfyUI) with MOSS-Image and native subgraph support. Tested: ComfyUI 0.43.0 / frontend 1.57.4.
2. Extract the release ZIP or clone this repository into `ComfyUI/custom_nodes/MOSS-Image-Character-Sheet-Designer`.
3. Install the four model files below. No additional Python packages are needed beyond the ComfyUI environment.
4. Restart ComfyUI normally and reload the browser.
5. Open [MOSS-Image Character Sheet Designer - Text or Image.json](examples/MOSS-Image%20Character%20Sheet%20Designer%20-%20Text%20or%20Image.json).

Find **MOSS-Image Character Sheet Designer** under `MOSS-Image/Character Sheet`. Other template nodes, including Generate Text, Switch and Seed, are ComfyUI core nodes. Update ComfyUI if they are missing.

## Required models

Paths are relative to ComfyUI. The template uses these filenames and subfolders; adjust loader selections if your installation differs. Weights are not included or downloaded automatically.

| Component / 種類 | Download | Destination / 配置先 |
|---|---|---|
| Diffusion model | [moss_image_sft_int8_convrot.safetensors](https://huggingface.co/Comfy-Org/MOSS-Image/resolve/main/diffusion_models/moss_image_sft_int8_convrot.safetensors) | `models/diffusion_models/MOSS-Image/` |
| Text encoder / CLIP | [qwen3.5_9b_int8_convrot.safetensors](https://huggingface.co/Comfy-Org/MOSS-Image/resolve/main/text_encoders/qwen3.5_9b_int8_convrot.safetensors) | `models/text_encoders/` |
| VAE | [full_encoder_small_decoder.safetensors](https://huggingface.co/black-forest-labs/FLUX.2-small-decoder/resolve/main/full_encoder_small_decoder.safetensors) | `models/vae/` |
| 8-step LoRA | [lora_latest.safetensors](https://huggingface.co/lodestones/MOSS-Image-SFT-8-steps-dmd/resolve/main/lora_latest.safetensors) | `models/loras/moss_image/` |


Load CLIP type must be **`moss_image`**. The tested encoder supplies vision for Generate Text, so the template needs no separate CLIP Vision loader. LoRA strength **0.7** follows the [author's recommendation](https://huggingface.co/lodestones/MOSS-Image-SFT-8-steps-dmd). See [OpenMOSS](https://github.com/OpenMOSS/MOSS-Image) and the [Comfy-Org model collection](https://huggingface.co/Comfy-Org/MOSS-Image).

## Text or image workflow

The template groups model loading, image description and sampling in a subgraph. The Designer stays outside for direct operation. The supplied template's node names, placement and settings are preserved.

1. **Text:** set the subgraph's `enable_prompt_enhancer` switch to **false** and enter a description in **Character Profile**. Image captioning is bypassed.
2. **Image:** select a file in **Load Image** and set `enable_prompt_enhancer` to **true**. Inside the subgraph, Generate Text describes the image after resizing its maximum dimension to 1024 pixels. Its prompt can contain a requested change; the connected system prompt provides description instructions.
3. Choose illustrated views or a preset. Optionally set part prompts, global style and Clothing shape.
4. Set the seed and run. Defaults: five views, no added global style, **Euler / simple, 8 steps, CFG 2, LoRA 0.7**.

**Describe the subject and outfit only. Leave backgrounds, scenery and unrelated objects out of Character Profile.** This node does not remove backgrounds or guarantee that background instructions are ignored. A selected background is a generation instruction, not a segmentation mask.

Try another seed when results vary; optionally compare CFG 3. It improved some tested clothing details but does not guarantee correct viewpoints. More steps add rendering time. These are project starting settings, not a universal optimum.

## Designer controls

| Control | Purpose |
|---|---|
| Illustrated cards | Six head views, three full-body views, front/back garments, hands and footwear: up to 13 panels |
| Presets | Common selections that can be customized |
| Auto / Manual | Auto scales the grouped layout within 1 / 1.5 / 2 / 4 MP; Manual retains requested dimensions |
| Clothing shape | Auto, pants, or skirt/robe; clothing panels always request garments alone, laid flat |
| Layout | Guide illustrations and panel positions; these are not generated images |
| Part prompts / Style | Details for selected parts and a global rendering style |
| Settings | Advanced options, generated prompt inspection and saved JSON recovery |

UI language follows ComfyUI. State is saved per node and restored with the workflow. Invalid saved JSON is reported instead of silently replaced.

## Inputs, outputs and encoder reuse

| Socket | Type | Meaning |
|---|---|---|
| `prompt` input | STRING, required | External subject/outfit description; no duplicate internal text box |
| `state_json` | Saved widget | View/layout/style settings managed by the UI |
| `prompt` output | STRING | Single-view caption or MOSS Layout JSON |
| `width`, `height` outputs | INT | Dimensions for EmptyFlux2LatentImage |

Connect `prompt` **directly to positive CLIPTextEncode**, and dimensions to EmptyFlux2LatentImage. Keep negatives in a separate CLIPTextEncode. The Designer has no negative output or visible CLIP input.

For clothing or three or more head views, the Designer reuses the MOSS CLIP connected to the downstream positive CLIPTextEncode. Native Generate Text extracts part-specific features before sheet compilation. No separate LLM model, download or external service is added. Single-view and working three/five/seven-view presets bypass internal analysis.

Image captioning and part analysis are separate operations; complex image-based sheets can use both. Warmed image captioning alone took roughly 3–6 seconds locally (about 6.3 seconds for the selected instruction). Loading, internal analysis and diffusion rendering are additional. ComfyUI can reuse cached analysis for seed changes while the cache remains valid. Performance varies by hardware and model state.

## Quality and troubleshooting

- Exact profiles, three-quarter views, head counts and all-13 layouts can still vary. Use 4 MP or fewer views when dense layouts lose detail.
- Garment extraction improved across tested subjects and seeds, but body/neck fragments, shape errors or changed clothing can remain. There is no Worn mode.
- Image descriptions lose information; unseen sides are inferred and lettering can change. This workflow does not perform direct image edits.
- `E_PROMPT_EMPTY`: connect a nonempty STRING, or select an image and enable the image branch.
- `E_ANALYSIS_ENCODER`: connect directly to one MOSS CLIPTextEncode and check the CLIP type.
- Invalid feature JSON fails explicitly without hidden corrective retries. Inspect the input and retry.
- Missing models/nodes: check paths above and update ComfyUI. Load Image's default filename is a placeholder; select your own image.
- Old saved character/outfit fields are retained for compatibility, but the connected prompt is authoritative. Legacy `clothing_mode` is removed during normalization. Move old negative-output connections to a separate encoder; connected links are not silently deleted.

Python/DOM tests and local GPU comparisons cover contracts, controls, text/image workflows and multiple subjects/seeds. They do not establish perfect visual compliance. See [validation](docs/TESTING.md). Physical Windows IME and Nodes 2.0 acceptance are not claimed.

## License

Original code and documentation use the scoped [MIT license](LICENSE). Artwork and third-party materials have separate rights: read [NOTICE.md](NOTICE.md). Model weights retain their authors' licenses; this repository does not grant model or generated-image rights.
