import tkinter as tk
from tkinter import filedialog
import sounddevice as sd
import numpy as np
import threading
import subprocess
import matplotlib
import mido
import time

matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

GM_PROGRAM_NAMES = [
    "Acoustic Grand Piano", "Bright Acoustic Piano", "Electric Grand Piano", "Honky-tonk Piano",
    "Electric Piano 1", "Electric Piano 2", "Harpsichord", "Clavinet", "Celesta", "Glockenspiel",
    "Music Box", "Vibraphone", "Marimba", "Xylophone", "Tubular Bells", "Dulcimer",
    "Drawbar Organ", "Percussive Organ", "Rock Organ", "Church Organ", "Reed Organ",
    "Accordion", "Harmonica", "Tango Accordion", "Acoustic Guitar (nylon)", "Acoustic Guitar (steel)",
    "Electric Guitar (jazz)", "Electric Guitar (clean)", "Electric Guitar (muted)", "Overdriven Guitar",
    "Distortion Guitar", "Guitar harmonics", "Acoustic Bass", "Electric Bass (finger)",
    "Electric Bass (pick)", "Fretless Bass", "Slap Bass 1", "Slap Bass 2", "Synth Bass 1",
    "Synth Bass 2", "Violin", "Viola", "Cello", "Contrabass", "Tremolo Strings",
    "Pizzicato Strings", "Orchestral Harp", "Timpani", "String Ensemble 1", "String Ensemble 2",
    "Synth Strings 1", "Synth Strings 2", "Choir Aahs", "Voice Oohs", "Synth Choir",
    "Orchestra Hit", "Trumpet", "Trombone", "Tuba", "Muted Trumpet", "French Horn",
    "Brass Section", "Synth Brass 1", "Synth Brass 2", "Soprano Sax", "Alto Sax",
    "Tenor Sax", "Baritone Sax", "Oboe", "English Horn", "Bassoon", "Clarinet",
    "Piccolo", "Flute", "Recorder", "Pan Flute", "Blown Bottle", "Shakuhachi",
    "Whistle", "Ocarina", "Lead 1 (square)", "Lead 2 (sawtooth)", "Lead 3 (calliope)",
    "Lead 4 (chiff)", "Lead 5 (charang)", "Lead 6 (voice)", "Lead 7 (fifths)", "Lead 8 (bass + lead)",
    "Pad 1 (new age)", "Pad 2 (warm)", "Pad 3 (polysynth)", "Pad 4 (choir)", "Pad 5 (bowed)",
    "Pad 6 (metallic)", "Pad 7 (halo)", "Pad 8 (sweep)", "FX 1 (rain)", "FX 2 (soundtrack)",
    "FX 3 (crystal)", "FX 4 (atmosphere)", "FX 5 (brightness)", "FX 6 (goblins)",
    "FX 7 (echoes)", "FX 8 (sci-fi)", "Sitar", "Banjo", "Shamisen", "Koto", "Kalimba",
    "Bag pipe", "Fiddle", "Shanai", "Tinkle Bell", "Agogo", "Steel Drums", "Woodblock",
    "Taiko Drum", "Melodic Tom", "Synth Drum", "Reverse Cymbal", "Guitar Fret Noise",
    "Breath Noise", "Seashore", "Bird Tweet", "Telephone Ring", "Helicopter", "Applause", "Gunshot"
]

class MidiWaveformApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🎹 MIDI Waveform Player")
        self.root.geometry("900x800")

        self.running = False
        self.device_index = tk.IntVar(value=0)
        self.volume = 0
        self.channel_programs = {}  # チャンネル: プログラム番号
        self.soundfont_path = "soundfont.sf2"

        self.create_widgets()
        self.setup_plot()

    def create_widgets(self):
        tk.Button(self.root, text="🔍 MIDIファイル選択", command=self.select_midi).pack(pady=5)

        tk.Label(self.root, text="🎧 録音デバイス番号：").pack()
        self.device_entry = tk.Entry(self.root, textvariable=self.device_index)
        self.device_entry.pack(pady=5)

        tk.Button(self.root, text="🎼 SoundFontを選択", command=self.select_soundfont).pack(pady=5)

        tk.Button(self.root, text="▶ 再生開始", command=self.start).pack(pady=5)
        tk.Button(self.root, text="■ 停止", command=self.stop).pack(pady=5)

        self.note_label = tk.Label(self.root, text="♪ ノート: ", font=("Consolas", 14))
        self.note_label.pack(pady=5)

        self.volume_bar = tk.Canvas(self.root, width=200, height=20, bg="black")
        self.volume_rect = self.volume_bar.create_rectangle(0, 0, 0, 20, fill="green")
        self.volume_bar.pack(pady=5)

        self.instrument_label = tk.Label(self.root, text="🎻 使用楽器:")
        self.instrument_label.pack(pady=5)

    def setup_plot(self):
        self.fig, self.ax = plt.subplots(figsize=(6, 3))
        self.ax.set_ylim(-1, 1)
        self.line, = self.ax.plot(np.zeros(1024))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack()
        self.canvas.draw()

    def select_midi(self):
        self.midi_path = filedialog.askopenfilename(filetypes=[("MIDI files", "*.mid *.midi")])
        if self.midi_path:
            self.parse_instruments()

    def select_soundfont(self):
        path = filedialog.askopenfilename(filetypes=[("SoundFont files", "*.sf2")])
        if path:
            self.soundfont_path = path
            print(f"🎼 SoundFont選択: {path}")

    def parse_instruments(self):
        self.channel_programs = {}
        try:
            midi = mido.MidiFile(self.midi_path)
            for msg in midi:
                if msg.type == "program_change":
                    self.channel_programs[msg.channel] = msg.program
            display = "\n".join(
                [f"Ch{ch+1}: Program {prog} - {GM_PROGRAM_NAMES[prog]}" for ch, prog in self.channel_programs.items()]
            )
            self.instrument_label.config(text=f"🎻 使用楽器:\n{display}")
        except Exception as e:
            self.instrument_label.config(text=f"⚠ 楽器情報の取得に失敗: {e}")

    def start(self):
        if not hasattr(self, "midi_path"):
            print("⚠ MIDIファイルが選択されていません")
            return
        self.running = True
        threading.Thread(target=self.play_midi, daemon=True).start()
        self.update_plot()
        self.update_note()

    def stop(self):
        self.running = False

    def play_midi(self):
        subprocess.run(["fluidsynth", "-ni", self.soundfont_path, self.midi_path])

    def update_plot(self):
        if not self.running:
            return
        try:
            data = sd.rec(512, samplerate=44100, channels=1, dtype="float32", device=self.device_index.get())
            sd.wait()
            self.line.set_ydata(np.interp(np.linspace(0, len(data)-1, 1024), np.arange(len(data)), data.flatten()))
            self.canvas.draw()
            vol = min(max(np.abs(data).max(), 0), 1)
            self.volume_bar.coords(self.volume_rect, 0, 0, 200 * vol, 20)
        except Exception as e:
            print(f"⚠ 波形描画エラー: {e}")
        self.root.after(16, self.update_plot)  # 約60FPS相当

    def update_note(self):
        if not self.running or not hasattr(self, "midi_path"):
            return
        try:
            midi = mido.MidiFile(self.midi_path)
            notes = [msg.note for msg in midi if msg.type == "note_on"]
            if notes:
                note = notes[int(time.time() * 2) % len(notes)]
                self.note_label.config(text=f"♪ ノート: {mido.get_note_name(note)}")
        except Exception as e:
            self.note_label.config(text=f"⚠ ノート取得エラー: {e}")
        self.root.after(1000, self.update_note)

if __name__ == "__main__":
    root = tk.Tk()
    app = MidiWaveformApp(root)
    root.mainloop()
