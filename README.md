# 🎹 Simple midi Player

![version](https://img.shields.io/badge/version-1.6.2-blue.svg)
![platform](https://img.shields.io/badge/platform-Windows%2010+-lightgrey.svg)
![license](https://img.shields.io/badge/license-Closed%20Source-red.svg)

**Simple midi Player** は、Windows向けの軽量MIDI再生プレイヤーです。  
シンプルな操作性と、再生位置の指定・一時停止・再開・楽器名表示など、視覚的かつ実用的な機能を備えています。

---

## 🔧 主な機能

- 🎵 MIDIファイルの読み込みと再生
- ⏸ 一時停止 → ▶ 再開が可能
- ⏩ 任意の時間から再生（シーク機能）
- ⏱ 再生時間をリアルタイム表示（1秒ごとに更新）
- 🎼 使用楽器（GM音源）を自動で表示
- 🎨 任意の SoundFont（`.sf2`）を選択可能
- 🪄 独自アイコン付きの `.exe` 配布（Python不要）
- 🖥 フルHD対応のGUI（1980×1080）

---

## <img width="596" height="473" alt="スクリーンショット 2025-08-08 024526" src="https://github.com/user-attachments/assets/63b276e2-4234-4da0-b13b-2051760e8d31" />


> 📸 Coming Soon!（GUIデザイン更新時に追加予定）

---

## 📥 ダウンロード

- 📦 [公式Wixサイト（最新版）](https://kunamaokunamao2828.wixsite.com/my-site-1)
- 📁 [GitHub Releases](https://github.com/KUNAOKUNAO/MIDI-Hakei-Player/releases/tag/v1.6.2)

---

## 📂 同梱ファイル

| ファイル名 | 内容 |
|------------|------|
| `MIDI_Hakei_Player.exe` | 実行ファイル（Python不要） |
| `soundfont.sf2` | サウンドフォント（MIDI音源） |
| `fluidsynth` | FluidSynthバイナリ一式 |
| `Piano.ico` | オリジナルアプリアイコン |
| `README.txt` | オフライン用概要説明 |
| `LICENSE.txt` | 利用規約・禁止事項など |

---

## 📝 使用方法

1. `MIDI_Hakei_Player.exe` をダブルクリックで起動
2. メニューから `.mid` ファイルを選択
3. 再生・停止・一時停止・再開を操作
4. 必要に応じて `.sf2` を変更（初回は `soundfont.sf2` を利用）

---

## ⚠ 注意事項

- `.sf2` ファイルが無い場合、音が鳴りません。必ず同じフォルダに配置してください。
- FluidSynth を使用しているため、**PATH に fluidsynth フォルダを追加**する必要がある場合があります。

### ✅ PATHの通し方（Windows）

1. `fluidsynth` フォルダの場所をコピー  
2. 「環境変数」→「Path」に追加  
3. コマンドプロンプトやPCを再起動

---

## 📃 ライセンス

このソフトは **無料でご利用いただけます**。  
ただし、以下の制限があります：

- 🔒 **再配布は禁止**
- 🛠 改変はOK（ただし配布NG）
- 商用利用は不可
- 詳細は [`LICENSE.txt`](./LICENSE.txt) を参照

---

## 📌 作者

**KUNAMAO**  
開発・公開：2025年  
ご連絡・要望は Wix または GitHub Issues にてお気軽にどうぞ！

---

🎵 あなたのMIDIライフに、もっと視覚と操作性を。  
**Simple midi Player** をよろしくお願いします！

