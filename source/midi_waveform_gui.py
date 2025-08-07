import tkinter as tk
from tkinter import filedialog
import sounddevice as sd
import numpy as np
import threading
import subprocess
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import mido

SOUNDFONT_FILE = "soundfont.sf2"  # 任意のSoundFontに変更

class MidiWaveformApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🎹 MIDI Waveform Player")

        self.running = False
        self.device_index = tk.IntVar(value=0)
        self.midi_path = None
        self.note_label = tk.StringVar()
        self.volume_level = tk.DoubleVar()

        self.create_widgets()
        self.setup_plot()

    def create_widgets(self):
        tk.Button(self.root, text="🔍 MIDIファイル選択", command=self.select_midi).pack(pady=5)

        tk.Label(self.root, text="🎧 録音デバイス番号：").pack()
        tk.Entry(self.root, textvariable=self.device_index).pack(pady=5)

        tk.Button(self.root, text="▶ 再生開始", command=self.start).pack(pady=5)
        tk.Button(self.root, text="■ 停止", command=self.stop).pack(pady=5)

        tk.Label(self.root, textvariable=self.note_label, font=("Consolas", 14)).pack()
        tk.Label(self.root, text="🔊 音量").pack()
        tk.Scale(self.root, variable=self.volume_level, from_=0, to=1, orient=tk.HORIZONTAL, resolution=0.01, length=300, state="disabled").pack()

    def setup_plot(self):
        self.fig, self.ax = plt.subplots(figsize=(6, 3))
        self.ax.set_ylim(-1, 1)
        self.line, = self.ax.plot(np.zeros(1024))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack()
        self.canvas.draw()

    def select_midi(self):
        self.midi_path = filedialog.askopenfilename(filetypes=[("MIDI files", "*.mid *.midi")])

    def start(self):
        if not self.midi_path:
            print("⚠ MIDIファイルが選択されていません")
            return
        self.running = True
        threading.Thread(target=self.play_midi, daemon=True).start()
        threading.Thread(target=self.analyze_midi, daemon=True).start()
        self.update_plot()

    def stop(self):
        self.running = False

    def play_midi(self):
        subprocess.run(["fluidsynth", "-ni", SOUNDFONT_FILE, self.midi_path])

    def update_plot(self):
        if not self.running:
            return
        try:
            data = sd.rec(1024, samplerate=44100, channels=1, dtype="float32", device=self.device_index.get())
            sd.wait()
            self.line.set_ydata(data.flatten())
            self.volume_level.set(np.max(np.abs(data)))
            self.canvas.draw()
        except Exception as e:
            print(f"⚠ 波形描画エラー: {e}")
        self.root.after(16, self.update_plot)  # 約60FPS

    def analyze_midi(self):
        try:
            mid = mido.MidiFile(self.midi_path)
            current_time = 0
            for msg in mid:
                if not self.running:
                    break
                current_time += msg.time
                if msg.type == 'note_on':
                    note_name = mido.get_note_name(msg.note)
                    self.note_label.set(f"♪ ノート: {note_name}")
                time_ms = int(current_time * 1000)
                self.root.after(time_ms, lambda: None)  # 遅延に合わせて
        except Exception as e:
            print(f"⚠ ノート解析エラー: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = MidiWaveformApp(root)
    root.mainloop()
