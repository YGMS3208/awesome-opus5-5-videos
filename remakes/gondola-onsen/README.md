# ゴンドラ落下 → 三角飛び3万回 → 露天風呂（ミスディレクション型ショート）

「落下エレベーターで直前ジャンプ」系の思考実験バズ動画の構造を借りて、
**サイバーパンク × 温泉PR** にアレンジした縦型ショート（1080×1920 / 30fps / 52秒）です。
映像はすべて Canvas 2D のコードで描画し、効果音・BGMも Python で合成しています（外部素材なし）。

| ファイル | 内容 |
|---|---|
| `index.html` | アニメーション本体。ブラウザで開けば音つきで再生（`audio.wav` を同じフォルダに置く） |
| `render.mjs` | Playwright でフレームを書き出し → ffmpeg で `video_silent.mp4` |
| `audio.py` | 効果音・BGMを合成して `audio.wav`（`timeline.json` の衝突タイミングに同期） |
| `fonts/` | Noto Sans JP / しっぽり明朝 / Orbitron（SIL OFL）。使う文字だけにサブセット化済み |
| `video.mp4` | 完成版（映像＋音） |

## 構成（元動画のフレームワークに対応）

| フェーズ | 秒 | 内容 | 音 |
|---|---|---|---|
| ① フック | 0–6 | 【思考実験】地上500mでゴンドラのワイヤーが切れたら？ 壁を蹴れば助かる？ | ワイヤー切断音 → 128BPMのビート、風切り音 |
| ② 科学的検証 | 6–16 | 解析モード（スロー×0.08）。落下 250km/h vs キック 15km/h のベクトルと棒グラフ → 「助からない」 | 心音・HUDの電子音・スタンプ |
| ③ シュールな超展開 | 16–30 | 「…ただし唯一の方法がある」→ ビルの間を三角飛び。回数カウンター 3万回、速度は 249.965km/h と微減、体温はどんどん上昇 | 150BPM、衝突ごとの金属音と火花 |
| ④ 意外な着地 | 30–38 | 体温 ERROR → ホワイトアウト → 流星になって夜の渓谷へ落下、湯けむりが上がる | 警報 → 着水の「ドーン」「ジュワァ」 |
| ⑤ 回収・PR | 38–52 | **0.5秒の無音** → 紅葉の露天風呂。手ぬぐいを頭にのせた本人と「体温 41.0℃ 適温」。<br>「時速250km出さなくても、芯まで温まります。」「この冬、ゆっくり癒やされに来てください。」 | ししおどし・湯の音・鈴虫・琴（都節音階） |

最後に小さく「※ゴンドラでのご来館はご遠慮ください。」と入れて、もう一度笑いを取ります。

## ナレーション原稿（読み上げを足す場合）

```
0:00  もし地上500mで、ゴンドラのワイヤーが切れたら。直前に壁を蹴れば助かるのか？
0:06  落下速度は時速250km。人間の脚力で壁を蹴っても、相殺できるのはわずか時速15km。
0:14  …助かりません。
0:16  ただし、唯一の方法があります。ビルの間を時速250kmでジグザグに三角飛びし続け、
      空気抵抗と摩擦熱で少しずつ減速すること。
0:26  飛び続けること3万回。摩擦熱で体温は限界を突破。
0:33  そして彼が着地した先は……
0:38  （無音）
0:40  湯煙谷温泉の、源泉かけ流し露天風呂。
0:45  時速250km出さなくても、芯まで温まります。
0:49  この冬、ゆっくり癒やされに来てください。
```

## 実在の温泉に差し替える

`index.html` 冒頭の `CONFIG`（`onsenName` / `onsenKana` / `onsenSub`）を書き換えてください。
フォントは今の台本の文字だけにサブセットしてあるので、新しい漢字が豆腐（□）になる場合は
`./fetch_fonts.sh` でフルセットのフォントを取得し直してください。

## 書き出し

```bash
./fetch_fonts.sh            # 任意：フルフォントを取得（文言を変えたとき）
node render.mjs --stills 3,15,28,46   # 静止画チェック（stills/ に出力、timeline.json も生成）
python3 audio.py            # audio.wav を合成
node render.mjs             # video_silent.mp4 を書き出し（約4分）
ffmpeg -i video_silent.mp4 -i audio.wav -c:v copy -c:a aac -b:a 192k -shortest video.mp4
```

## 実写系AIで作り直すときのプロンプト（Midjourney / Runway / Kling / Luma）

コード版の各シーンは、以下のキービジュアルとそのまま対応します。

1. **フック** — `Cinematic vertical shot (9:16), a futuristic cyberpunk window cleaning gondola falling rapidly between hyper-dense neon skyscrapers at night, a salaryman in a suit and yellow safety helmet on board, intense motion blur, wet glass reflecting neon signs, wind rushing upward, blade runner aesthetics, photorealistic --ar 9:16`
2. **科学的検証** — `Vertical 9:16, frozen bullet-time moment, holographic HUD overlay with a red downward velocity vector labeled 250 km/h and a tiny green vector labeled 15 km/h, worker clinging to a tilted gondola, extreme perspective down into a glowing magenta abyss --ar 9:16`
3. **超展開** — `Dynamic action (9:16), a man in a dark business suit ricocheting in a zigzag between two skyscraper glass walls at supersonic speed, golden friction sparks bursting at each wall impact, glowing zigzag light trail, shockwave rings, anime live-action style --ar 9:16`
4. **大気圏突入** — `Vertical 9:16, a white-hot meteor-like light trail falling out of a dark sky into a misty pine forest valley at night, steam explosion on impact, cold blue mist vs warm golden light --ar 9:16`
5. **オチ** — `Serene vertical shot (9:16), traditional Japanese open-air hot spring at twilight surrounded by red autumn maple leaves, stone lantern glowing, bamboo shishi-odoshi, a man relaxing with a folded towel on his head, a yellow safety helmet left on a rock, gentle steam, 4k travel commercial --ar 9:16`

編集のポイント：⑤に入る瞬間の **完全な無音（0.5秒）** と、ししおどしの「コーン」で空気を切り替えるのがいちばん効きます。
