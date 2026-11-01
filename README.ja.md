# MOSS-Image Character Sheet Designer v1.0

[English](README.md) · [ワークフローをダウンロード](https://github.com/ukr8b3g-cmyk/MOSS-Image-Character-Sheet-Designer/releases/download/v1.0/MOSS-Image-Character-Sheet-Designer-v1.0.json) · [リリース](https://github.com/ukr8b3g-cmyk/MOSS-Image-Character-Sheet-Designer/releases)

テキストの説明、またはMOSSのテキストエンコーダーで文章化した画像から、キャラクター設定シートを生成するComfyUIノードです。[H3版](https://github.com/ukr8b3g-cmyk/H3-Character-Sheet-Designer)と[Qwen-Image 2.1版](https://github.com/ukr8b3g-cmyk/Qwen-Image-2.1-Character-Sheet-Designer)を基に、図付きビュー選択、部位別プロンプト、スタイル、最大**13ビュー**のAuto／Manual配置に対応します。

## 重要：画像は文章に変換してから生成します

**このワークフローはテキストからの画像生成です。H3版・Qwen版と異なり、入力画像をMOSSの生成用リファレンス画像として直接渡しません。**

- **テキスト入力：** Character Profileへ人物と衣装の説明を入力します。基本となる入力方法です。
- **画像入力：** `enable_prompt_enhancer`を有効にします。既存のMOSSテキストエンコーダーで画像を解析し、その説明文から新しいシートを生成します。

**入力画像 → エンコーダーで解析 → 説明文 → MOSSで新規T2I生成**

元画像の画素やキャラクターの完全保持は保証しません。顔、衣装、色、装飾、文字、見えていない背面などは変わる場合があります。直接の画像編集や、生成時に元画像を直接参照する方式ではありません。上記の**1つのワークフロー**でテキスト／画像を切り替えられます。複数のテンプレートから選ぶ必要はありません。

Character Profileには**1人のキャラクターの外見だけ**を入力してください。顔・髪・体格・衣装・装飾を中心とし、背景・風景・無関係な物・別人物は入れないでください。

<img width="1774" height="818" alt="Clip_42" src="https://github.com/user-attachments/assets/c9b643e0-683f-41f2-ac2e-fa6455191dc2" />

## バージョン1.0

ノードと製品版は**v1.0**です。内部プロンプト契約の**moss-sheet-1.4.1**は別の実装番号です。今回は配布ファイルと説明を整理し、ノードの版表示を揃えました。生成処理と配布ワークフローの設定は変更していません。従来の指示保持修正も引き継いでいます。修正履歴と制約は[CHANGELOG](CHANGELOG.md)を参照してください。

## 導入と必要モデル

1. MOSS-Image・標準サブグラフ対応の[ComfyUI](https://github.com/Comfy-Org/ComfyUI)を用意します。確認環境はComfyUI 0.43.0 / frontend 1.57.4です。
2. ZIPを展開するかcloneし、`ComfyUI/custom_nodes/MOSS-Image-Character-Sheet-Designer`へ配置します。独自の追加Pythonパッケージはありません。
3. 下記4ファイルを配置します。配置が異なる場合はローダーの選択を合わせてください。重みは同梱・自動ダウンロードしません。
4. ComfyUIを通常の方法で再起動し、ブラウザーを再読み込みします。
5. [Text or Imageテンプレート](examples/MOSS-Image%20Character%20Sheet%20Designer%20-%20Text%20or%20Image.json)を開きます。

| Component / 種類 | Download | Destination / 配置先 |
|---|---|---|
| Diffusion model | [moss_image_sft_int8_convrot.safetensors](https://huggingface.co/Comfy-Org/MOSS-Image/resolve/main/diffusion_models/moss_image_sft_int8_convrot.safetensors) | `models/diffusion_models/MOSS-Image/` |
| Text encoder / CLIP | [qwen3.5_9b_int8_convrot.safetensors](https://huggingface.co/Comfy-Org/MOSS-Image/resolve/main/text_encoders/qwen3.5_9b_int8_convrot.safetensors) | `models/text_encoders/` |
| VAE | [full_encoder_small_decoder.safetensors](https://huggingface.co/black-forest-labs/FLUX.2-small-decoder/resolve/main/full_encoder_small_decoder.safetensors) | `models/vae/` |
| 8-step LoRA | [lora_latest.safetensors](https://huggingface.co/lodestones/MOSS-Image-SFT-8-steps-dmd/resolve/main/lora_latest.safetensors) | `models/loras/moss_image/` |


Load CLIPのtypeは **`moss_image`**。確認済みTEの画像理解機能を共有するため、別のCLIP Visionは不要です。LoRA強度 **0.7** は[作者の案内](https://huggingface.co/lodestones/MOSS-Image-SFT-8-steps-dmd)に基づきます。[OpenMOSS公式](https://github.com/OpenMOSS/MOSS-Image)も参照してください。

ノードは`MOSS-Image/Character Sheet`の **MOSS-Image Character Sheet Designer v1.0**です。Generate Text、Switch、Seedなど、他のテンプレート内ノードはComfyUI標準です。不足する場合はComfyUIを更新してください。

## テキスト／画像の使い方

モデル読込・画像の文章化・生成をサブグラフにまとめています。提供テンプレートのノード名・配置・設定は保持しています。

1. **テキストから:** サブグラフの`enable_prompt_enhancer`を **false** にし、**Character Profile**に人物・衣装の説明を入力します。画像の文章化は実行しません。
2. **画像から:** **Load Image**で画像を選び、`enable_prompt_enhancer`を **true** にします。内部で最大辺1024pxに縮小してGenerate Textへ渡します。必要な変更指示はそのpromptへ入力できます。画像説明用system promptは接続済みです。
3. Designerのカード／プリセットでビューを選び、必要に応じて部位の補足、スタイル、Clothing shapeを設定します。
4. seedを設定して実行します。初期値は5ビュー、追加スタイルなし、**Euler / simple、8 steps、CFG 2、LoRA 0.8**です。

**Character Profileには被写体・衣装の特徴だけを入力し、背景・風景・無関係な物は入れないでください。** 背景削除や、入力中の背景指定を確実に無視する処理はありません。背景色の選択は生成指示であり、切り抜きマスクではありません。

不安定な場合はまずseedを変え、必要ならCFG 3と比較してください。一部では衣服の欠落が改善しましたが、向きの誤りを必ず解消する設定ではありません。ステップ増加は生成時間に影響します。初期値は本プロジェクトの開始設定です。

## 操作と入出力

| 項目 | 用途 |
|---|---|
| カード | 頭6面・全身3面・衣装前後・手・履物の最大13パネル |
| Auto / Manual | Autoは1 / 1.5 / 2 / 4 MPに全体を等比縮小。Manualは指定寸法を保持 |
| Clothing shape | Auto / pants / skirt・robe。衣装は常に服だけの平置き指定 |
| Layout | 配置ガイド。人形は生成結果や生成へ渡す参照画像ではありません |
| Part prompts / Style | 選択部位の補足と全体スタイル |
| Settings | 詳細設定、警告、保存JSONの復旧 |

UI言語はComfyUIの設定に従います。設定はノードごとに保存し再読込で復元します。不正なJSONを勝手に置き換えることはありません。

- 入力`prompt`: 外部STRING必須。Designer内部に重複した文章欄はありません。
- `state_json`: UIが管理する保存データ。
- 出力`prompt`: 単一ビューのcaption、または複数ビュー用MOSS Layout JSON。
- 出力`width` / `height`: EmptyFlux2LatentImageへ渡すINT。

外部`prompt`の上限は **2,000 UTF-16単位**です（絵文字などは通常2単位）。MOSSのトークン上限ではなく、この拡張の文字数制限です。超過・不正なUnicodeは内部解析の前に拒否し、入力を勝手に切り詰めません。

Settingsは保存JSONの復旧欄で、実行時の最終プロンプト表示機能ではありません。配置プレビューには外部promptやTEの解析結果は含まれません。

**prompt出力はpositiveのCLIPTextEncodeへ直接接続**してください。negativeは別のCLIPTextEncodeへ入力します。Designerにはnegative出力や可視CLIP入力はありません。

衣装を含む選択、または頭3面以上では、接続先MOSS CLIPを内部の標準Generate Textでも流用し、部位別の特徴を整理します。別のLLMモデル・ダウンロード・外部送信はありません。単体・全身3面・5面・7面の既存プリセットでは内部整理を使いません。

画像の文章化と部位整理は別処理です。複雑な画像入力シートでは両方が動きます。ローカルの温まったモデルでは画像の文章化単独で約3〜6秒、採用指示で約6.3秒でした。初回ロード・部位整理・生成時間は別です。同一入力でseedだけ変える場合、キャッシュが有効な間は解析を再利用できます。時間は機材とモデル状態で変わります。

## 制約とエラー

- 横顔・斜め・頭の枚数・全13面の向きは完全には安定していません。密度が高く細部が小さい場合は4 MPか、ビューを減らしてください。
- 服だけの生成は複数被写体・seedで改善しましたが、首や身体の一部、形状誤り、衣装変更が残る場合があります。Wornモードはありません。
- 画像入力は説明文を経由するため、細部・文字・見えない面の正確な再現は保証しません。
- `E_PROMPT_EMPTY`: 空でないSTRINGを接続するか、画像を選択して画像側へ切替。
- `E_ANALYSIS_ENCODER`: 1つのMOSS CLIPTextEncodeへ直接接続し、CLIPのtypeを確認。
- 特徴JSONが不正な場合は明示的に失敗します。自動的に修正文を重ねる再試行はありません。
- Load Imageの初期ファイル名は仮置きです。画像モードでは自分の画像を選択してください。
- 旧人物・衣装データは互換保持しますが、生成は接続したpromptを使用。旧clothing_modeは正規化で除去。旧negative出力の接続は外部negative欄へ移してください。接続済みリンクは勝手に削除しません。

Python・DOMと、複数被写体／seedのローカルGPU比較を実施済みです。完全な画質合格を意味しません。[検証範囲](docs/TESTING.md)を参照してください。実Windows IME・Nodes 2.0は受入未確認です。

## ライセンス

独自コード・文書は適用範囲を限定した[MIT](LICENSE)です。画像・第三者素材について[NOTICE.md](NOTICE.md)も確認してください。モデル重みは各作者のライセンスに従います。
