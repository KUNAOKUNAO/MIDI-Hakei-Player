import numpy as np
import matplotlib.pyplot as plt
import sounddevice as sd
import fluidsynth
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox

print("✅ スクリプト開始")

# === 設定 ===
SOUNDFONT_FILE = "soundfont.sf2"
SAMPLE_RATE = 44100

# === ファイル選択 ===
root = tk.Tk()
root.attributes("-topmost", True)
root.withdraw()

print("📂 ファイル選択ダイアログ表示")

midi_path = filedialog.askopenfilename(
    title="再生するMIDIファイルを選んでください",
    filetypes=[("MIDI files", "*.mid *.midi")]
)

print("📁 選ばれたMIDIファイル:", midi_path)

if not midi_path:
    print("❌ ファイルが選ばれませんでした。終了します。")
    exit()

# === FluidSynth設定 ===
try:
    print("🎹 FluidSynth 初期化中")
    fs = fluidsynth.Synth(samplerate=SAMPLE_RATE)
    fs.start(driver="dsound")
    sfid = fs.sfload(SOUNDFONT_FILE)
    fs.program_select(0, sfid, 0, 0)
except Exception as e:
    print("❌ FluidSynthの初期化に失敗:", e)
    exit()

# === MIDI再生関数 ===
def play_midi():
    print("▶ MIDI再生開始")
    try:
        fs.midi_file_play(midi_path)
    except Exception as e:
        print("❌ MIDI再生エラー:", e)

# === 波形描画用コールバック ===
def audio_callback(indata, frames, time_info, status):
    if status:
        print("⚠️ 音声ステータス:", status)
    y = indata[:, 0]
    line.set_ydata(y)
    fig.canvas.draw()
    fig.canvas.flush_events()

# === 波形グラフ描画の準備 ===
try:
    print("📈 波形描画準備")
    plt.ion()
    fig, ax = plt.subplots()
    x = np.arange(1024)
    y = np.zeros(1024)
    line, = ax.plot(x, y)
    ax.set_ylim([-1, 1])
    ax.set_xlim([0, 1024])
    ax.set_title("🎧 MIDIリアルタイム波形表示")
    ax.set_facecolor("black")
    line.set_color("#88C0D0")
except Exception as e:
    print("❌ matplotlibの初期化に失敗:", e)
    exit()

# === スレッドでMIDI再生開始 ===
threading.Thread(target=play_midi).start()

# === 音声取得＋波形アニメーション ===
try:
    with sd.InputStream(channels=1, callback=audio_callback, samplerate=SAMPLE_RATE, blocksize=1024):
        print("🎧 波形アニメーション開始中...")
        while fs.get_status():
            time.sleep(0.1)
except Exception as e:
    print("❌ 音声ストリームに失敗:", e)

fs.delete()
print("✅ MIDI再生＆波形アニメーション終了")
