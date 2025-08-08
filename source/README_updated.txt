🎹 Simple midi Player - v2.0.0
Simple midi Player は、MIDIファイルを簡単に再生できる Windows向けGUIソフトです。
再生位置の指定、一時停止・再開、再生時間・BPM・キーのリアルタイム表示など、軽量ながら実用的な機能を搭載しています。

✅ 主な機能（v2.0.0 現在）
🎵 MIDIファイルの読み込みと再生

⏯ 一時停止・再開機能

⏩ 任意の時間から再生（シーク対応）

⏱ 再生時間のリアルタイム表示（1秒ごと更新）

🎼 使用楽器（GM音源）の自動表示

🎵 MIDIの BPM と キー を自動解析・表示

🎨 SoundFont（.sf2）の選択に対応

🪄 GUIアイコン付きの .exe 配布（SMP_icon.ico）

🖥 フルHD対応 GUI（1980×1080）
※波形はソフトウェア安定のため一時的に削除されました。

🔧 今後追加予定の機能
使用楽器の手動変更UI

シークバー操作による位置移動

軽量音量バーまたはスペクトラムの復活

プレイリスト/設定保存機能

GUIデザインの刷新

💻 対応環境
Windows 10 以降（推奨）

Python 不要（.exe のみで動作可能）

📦 同梱ファイル一覧
ファイル名	説明
Simple_midi_Player.exe	本体実行ファイル
soundfont.sf2	サウンドフォント（音源）
SMP_icon.ico	アプリ用アイコン
fluidsynth	MIDI再生用ライブラリ

⚠️ 注意点（SoundFontとPATH）
このソフトは SoundFont（例: soundfont.sf2） を使って音を鳴らします。
以下のような問題が起きる場合があります：

症状	原因と対処法
音が出ない	soundfont.sf2 が存在しない、または破損している場合があります。同梱ファイルを確認してください。
FluidSynthが動かない	fluidsynth フォルダの場所を 環境変数 PATH に追加してください。

🛠 PATHの追加方法（Windows）
fluidsynth フォルダの場所を右クリック→「パスのコピー」

Windows 検索で「環境変数」と検索→「環境変数の編集」を開く

「システム環境変数」→「Path」を選択し「編集」→「新規」で貼り付け

OKで閉じて、PCまたはコマンドプロンプトを再起動

🔗 ダウンロード
公式Wixページ：https://kunamaokunamao2828.wixsite.com/my-site-1

GitHubリリースページ：準備中

📄 ライセンス
このソフトは無料でご利用いただけます

改変可能 / 再配布不可（LICENSE.txt を参照）

🎵 あなたのMIDIライフに、もっと視覚と操作性を。
Simple midi Player をよろしくお願いします！
