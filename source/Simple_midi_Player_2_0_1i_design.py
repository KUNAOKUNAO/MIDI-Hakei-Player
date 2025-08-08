import os
import json
import time
import signal
import psutil
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk

APP_TITLE = "Simple MIDI Player v2.0.3 (Instruments + BPM/Key)"
CONFIG_NAME = "mhp_config.json"
DRIVER_CHOICES = ["dsound", "wasapi", "portaudio"]

# ---- Try to import mido (for MIDI parsing) ----
try:
    import mido
    _HAVE_MIDO = True
except Exception:
    _HAVE_MIDO = False

# ---- GM Program Names (0-127) ----
GM_PROGRAMS = [
    "Acoustic Grand Piano","Bright Acoustic Piano","Electric Grand Piano","Honky-tonk Piano","Electric Piano 1","Electric Piano 2","Harpsichord","Clavinet",
    "Celesta","Glockenspiel","Music Box","Vibraphone","Marimba","Xylophone","Tubular Bells","Dulcimer",
    "Drawbar Organ","Percussive Organ","Rock Organ","Church Organ","Reed Organ","Accordion","Harmonica","Tango Accordion",
    "Acoustic Guitar (nylon)","Acoustic Guitar (steel)","Electric Guitar (jazz)","Electric Guitar (clean)","Electric Guitar (muted)","Overdriven Guitar","Distortion Guitar","Guitar harmonics",
    "Acoustic Bass","Electric Bass (finger)","Electric Bass (pick)","Fretless Bass","Slap Bass 1","Slap Bass 2","Synth Bass 1","Synth Bass 2",
    "Violin","Viola","Cello","Contrabass","Tremolo Strings","Pizzicato Strings","Orchestral Harp","Timpani",
    "String Ensemble 1","String Ensemble 2","SynthStrings 1","SynthStrings 2","Choir Aahs","Voice Oohs","Synth Voice","Orchestra Hit",
    "Trumpet","Trombone","Tuba","Muted Trumpet","French Horn","Brass Section","SynthBrass 1","SynthBrass 2",
    "Soprano Sax","Alto Sax","Tenor Sax","Baritone Sax","Oboe","English Horn","Bassoon","Clarinet",
    "Piccolo","Flute","Recorder","Pan Flute","Blown Bottle","Shakuhachi","Whistle","Ocarina",
    "Lead 1 (square)","Lead 2 (sawtooth)","Lead 3 (calliope)","Lead 4 (chiff)","Lead 5 (charang)","Lead 6 (voice)","Lead 7 (fifths)","Lead 8 (bass+lead)",
    "Pad 1 (new age)","Pad 2 (warm)","Pad 3 (polysynth)","Pad 4 (choir)","Pad 5 (bowed)","Pad 6 (metallic)","Pad 7 (halo)","Pad 8 (sweep)",
    "FX 1 (rain)","FX 2 (soundtrack)","FX 3 (crystal)","FX 4 (atmosphere)","FX 5 (brightness)","FX 6 (goblins)","FX 7 (echoes)","FX 8 (sci-fi)",
    "Sitar","Banjo","Shamisen","Koto","Kalimba","Bag pipe","Fiddle","Shanai",
    "Tinkle Bell","Agogo","Steel Drums","Woodblock","Taiko Drum","Melodic Tom","Synth Drum","Reverse Cymbal",
    "Guitar Fret Noise","Breath Noise","Seashore","Bird Tweet","Telephone Ring","Helicopter","Applause","Gunshot"
]

# ---------------- Config helpers ----------------
def config_path():
    try:
        base = os.path.dirname(os.path.abspath(__file__))
    except Exception:
        base = os.getcwd()
    return os.path.join(base, CONFIG_NAME)

def load_config():
    try:
        with open(config_path(), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_config(data):
    try:
        with open(config_path(), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

# ---------------- Simple tooltip ----------------
class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, _=None):
        if self.tip or not self.text:
            return
        x, y, cx, cy = self.widget.bbox("insert") or (0, 0, 0, 0)
        x += self.widget.winfo_rootx() + 20
        y += self.widget.winfo_rooty() + 25
        self.tip = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        lbl = ttk.Label(tw, text=self.text, padding=(8, 4))
        lbl.pack()

    def hide(self, _=None):
        if self.tip:
            self.tip.destroy()
            self.tip = None

# ---------------- Main App ----------------
class SimpleMIDIPlayer200Design:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("1040x600")
        self.root.minsize(940, 540)
        self.proc = None
        self.running = False
        self.paused = False

        # Load config
        self.cfg = load_config()
        self.sf2_path = self.cfg.get("soundfont")
        self.fs_exe_path = self.cfg.get("fluidsynth")
        self.audio_driver = tk.StringVar(value=self.cfg.get("audio_driver") or DRV_DEFAULT())
        self.gain = tk.DoubleVar(value=float(self.cfg.get("gain", 0.8)))

        self.last_midi_dir = self.cfg.get("last_midi_dir") or os.getcwd()
        self.last_sf2_dir = self.cfg.get("last_sf2_dir") or os.getcwd()
        self.last_fs_dir = self.cfg.get("last_fs_dir") or os.getcwd()

        self.selected_midi_path = None

        # Build UI
        self._init_style()
        self._build_ui()
        self._apply_state("stopped")

        # Shortcuts
        self.root.bind("<space>", self._toggle_pause_key)
        self.root.bind("<Control-o>", lambda e: self.pick_midi())
        self.root.bind("<Control-s>", lambda e: self.pick_sf2())

        self._set_status("準備OK")

    # ---------- Style / Dark mode ----------
    def _init_style(self):
        self.style = ttk.Style()
        try:
            if "vista" in self.style.theme_names():
                self.style.theme_use("vista")
        except Exception:
            pass

        self.style.configure("TFrame", padding=6)
        self.style.configure("Card.TFrame", relief="groove", borderwidth=1, padding=12)
        all_title_font = ("", 14, "bold")
        self.style.configure("Title.TLabel", font=all_title_font)
        self.style.configure("Status.TLabel", anchor="w")

        self.dark = tk.BooleanVar(value=bool(self.cfg.get("dark_mode", False)))
        self._apply_dark_mode_colors()

    def _apply_dark_mode_colors(self):
        dark = self.dark.get()
        if dark:
            bg = "#1f2329"; fg = "#e6e6e6"; card = "#2a2f36"; acc = "#3a3f46"
        else:
            bg = "#f7f7fa"; fg = "#222222"; card = "#ffffff"; acc = "#f0f0f5"

        self.root.configure(bg=bg)
        self.style.configure(".", background=bg, foreground=fg)
        self.style.configure("TFrame", background=bg)
        self.style.configure("Card.TFrame", background=card)
        self.style.configure("TLabel", background=bg, foreground=fg)
        self.style.configure("Title.TLabel", background=bg, foreground=fg)
        self.style.configure("TLabelframe", background=bg, foreground=fg)
        self.style.configure("TLabelframe.Label", background=bg, foreground=fg)
        self.style.configure("TButton", padding=(10, 4))
        self.style.map("TButton", background=[("active", acc)])

    # ---------- UI ----------
    def _build_ui(self):
        header = ttk.Frame(self.root, style="TFrame")
        header.pack(fill="x")
        ttk.Label(header, text="🎧 Simple MIDI Player", style="Title.TLabel").pack(side="left")
        ttk.Button(header, text="🌗 ダークモード", command=self.toggle_dark).pack(side="right")

        cards = ttk.Frame(self.root)
        cards.pack(fill="x", padx=10, pady=8)

        # Card: Paths
        path_card = ttk.Frame(cards, style="Card.TFrame")
        path_card.pack(side="left", fill="both", expand=True, padx=(0, 8))

        row = ttk.Frame(path_card); row.pack(fill="x", pady=2)
        b = ttk.Button(row, text="🧰 fluidsynth.exe", command=self.pick_fluidsynth); b.pack(side="left")
        Tooltip(b, "fluidsynth実行ファイルを選択")
        self.fs_label = ttk.Label(row, text=self._short(self.fs_exe_path) or "PATH を使用"); self.fs_label.pack(side="left", padx=10)

        row = ttk.Frame(path_card); row.pack(fill="x", pady=2)
        b = ttk.Button(row, text="🎹 SoundFont", command=self.pick_sf2); b.pack(side="left")
        Tooltip(b, "SoundFont(.sf2) を選択")
        self.sf_label = ttk.Label(row, text=self._short(self.sf2_path) or "未選択"); self.sf_label.pack(side="left", padx=10)

        row = ttk.Frame(path_card); row.pack(fill="x", pady=2)
        b = ttk.Button(row, text="🎵（任意）選び直す", command=self.pick_midi); b.pack(side="left")
        Tooltip(b, "必要なら手動でMIDIを選び直し")
        self.midi_label = ttk.Label(row, text="未選択"); self.midi_label.pack(side="left", padx=10)

        # Card: Settings
        set_card = ttk.Frame(cards, style="Card.TFrame")
        set_card.pack(side="left", fill="y", padx=(8, 0))

        r = ttk.Frame(set_card); r.pack(fill="x", pady=4)
        ttk.Label(r, text="Audio Driver").pack(side="left")
        self.driver_cmb = ttk.Combobox(r, values=DRIVER_CHOICES, textvariable=self.audio_driver, width=12, state="readonly")
        self.driver_cmb.pack(side="left", padx=6)
        self.driver_cmb.bind("<<ComboboxSelected>>", lambda e: self._persist_controls())

        r = ttk.Frame(set_card); r.pack(fill="x", pady=4)
        ttk.Label(r, text="Gain").pack(side="left")
        self.gain_scale = ttk.Scale(r, from_=0.2, to=1.2, value=self.gain.get(), command=self._on_gain_change, length=180)
        self.gain_scale.pack(side="left", padx=6)
        self.gain_value = ttk.Label(r, text=f"{self.gain.get():.2f}"); self.gain_value.pack(side="left")

        # Controls card
        ctrl_card = ttk.Frame(self.root, style="Card.TFrame")
        ctrl_card.pack(fill="x", padx=10, pady=(0, 8))

        self.btn_play = ttk.Button(ctrl_card, text="▶ 再生（必要なら選択）", command=self.start, width=20)
        self.btn_pause = ttk.Button(ctrl_card, text="⏸ 一時停止", command=self.pause, width=12)
        self.btn_resume = ttk.Button(ctrl_card, text="⏵ 再開", command=self.resume, width=12)
        self.btn_stop = ttk.Button(ctrl_card, text="⏹ 停止", command=self.stop, width=12)
        self.btn_wait = ttk.Button(ctrl_card, text="⌛ 終了待ち", command=self.wait_until_finish, width=12)
        for w in (self.btn_play, self.btn_pause, self.btn_resume, self.btn_stop, self.btn_wait):
            w.pack(side="left", padx=6, pady=4)

        # Bottom area: Status + Meta + Instruments
        bottom = ttk.Frame(self.root, style="Card.TFrame")
        bottom.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # left: status & meta & button
        left_btm = ttk.Frame(bottom); left_btm.pack(side="left", fill="both", expand=True, padx=(0,8))
        self.status = ttk.Label(left_btm, text="待機中", style="Status.TLabel"); self.status.pack(fill="x")
        self.song_meta = ttk.Label(left_btm, text="Tempo: -  |  TS: -  |  Key: -")
        self.song_meta.pack(anchor="w", pady=(6,0))
        ttk.Button(left_btm, text="🎼 使用楽器を解析", command=self.analyze_instruments).pack(anchor="w", pady=6)

        # right: instruments tree
        right_btm = ttk.Frame(bottom); right_btm.pack(side="left", fill="both", expand=True)
        ttk.Label(right_btm, text="使用楽器（GM）").pack(anchor="w")
        cols = ("ch","bank","prog","name")
        self.tree = ttk.Treeview(right_btm, columns=cols, show="headings", height=12)
        for c, w in zip(cols, (50,60,60,240)):
            self.tree.heading(c, text={"ch":"Ch","bank":"Bank","prog":"Prog","name":"Name"}[c])
            self.tree.column(c, width=w, anchor="center" if c!="name" else "w")
        self.tree.pack(fill="both", expand=True)

        # Footer actions
        foot = ttk.Frame(self.root); foot.pack(fill="x", padx=10, pady=(0, 10))
        ttk.Button(foot, text="🧽 設定クリア", command=self.clear_memory).pack(side="left")

    def _short(self, path, maxlen=40):
        if not path:
            return ""
        p = os.path.abspath(path)
        return p if len(p) <= maxlen else ("…" + p[-maxlen:])

    def toggle_dark(self):
        self.dark.set(not self.dark.get())
        self.cfg["dark_mode"] = bool(self.dark.get())
        save_config(self.cfg)
        self._apply_dark_mode_colors()

    # ---------- Mechanics (2.0.0 concept) ----------
    def _finalize_ended_process(self):
        if self.proc is not None and self.proc.poll() is not None:
            self.proc = None
            self.running = False
            self.paused = False
            self._apply_state("stopped")
            self._set_status("停止/終了")

    def _build_cmd(self, midi_path):
        exe = self.fs_exe_path or "fluidsynth"
        driver = self.audio_driver.get().strip() or DRV_DEFAULT()
        gain = float(self.gain.get())
        sf2 = self.sf2_path
        if not sf2 or not os.path.exists(sf2):
            raise FileNotFoundError("SoundFont(.sf2) が未選択、または見つかりません。")
        if not midi_path or not os.path.exists(midi_path):
            raise FileNotFoundError("MIDI ファイルが見つかりません。")
        return [exe, "-a", driver, "-g", f"{gain:.2f}", "-ni", sf2, midi_path]

    def _poll_process(self):
        if self.proc is None:
            return
        if self.proc.poll() is None:
            self.root.after(300, self._poll_process)
            return
        self.running = False
        self.paused = False
        self.proc = None
        self._apply_state("stopped")
        self._set_status("停止/終了")

    # ---------- MIDI Instrument & Meta analysis ----------
    def analyze_instruments(self):
        self.tree.delete(*self.tree.get_children())
        midi = self.selected_midi_path
        if not midi or not os.path.exists(midi):
            messagebox.showinfo("情報", "MIDI を先に選択してください。")
            return
        if not _HAVE_MIDO:
            messagebox.showwarning("mido が必要",
                                   "使用楽器・テンポ/キーを解析するには mido が必要です。\n\npip install mido\n\nを実行してからお試しください。")
            return

        try:
            used = extract_instruments(midi)
            meta = extract_meta(midi)
        except Exception as e:
            messagebox.showerror("解析エラー", str(e))
            return

        # 表示（楽器）
        if not used:
            self.tree.insert("", "end", values=("-", "-", "-", "(検出なし)"))
        else:
            for ch in sorted(used.keys()):
                bank, prog, name = used[ch]
                self.tree.insert("", "end", values=(ch, bank, prog, name))
        # 表示（メタ）
        self.song_meta.config(
            text=f"Tempo: {meta['bpm']} BPM  |  TS: {meta['time_sig']}  |  Key: {meta['key']}"
                 + (f"  (+{meta['tempo_changes']} tempo changes)" if meta['tempo_changes'] else "")
        )

    def start(self):
        self._finalize_ended_process()
        if self.proc:
            self.stop()

        # 必要なら選択
        if not self._ensure_midi_selected():
            return
        midi = self.selected_midi_path

        # 再生前に解析を自動実行（midoがある場合だけ）
        if _HAVE_MIDO:
            try:
                used = extract_instruments(midi)
                meta = extract_meta(midi)
                self.tree.delete(*self.tree.get_children())
                for ch in sorted(used.keys()):
                    bank, prog, name = used[ch]
                    self.tree.insert("", "end", values=(ch, bank, prog, name))
                self.song_meta.config(
                    text=f"Tempo: {meta['bpm']} BPM  |  TS: {meta['time_sig']}  |  Key: {meta['key']}"
                         + (f"  (+{meta['tempo_changes']} tempo changes)" if meta['tempo_changes'] else "")
                )
            except Exception:
                pass  # 解析失敗は無視して再生継続

        try:
            cmd = self._build_cmd(midi)
        except Exception as e:
            messagebox.showerror("起動エラー", str(e))
            return

        try:
            creation = (subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0)
            self.proc = subprocess.Popen(
                cmd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creation,
                close_fds=True,
            )
            self.running = True
            self.paused = False
            self._apply_state("playing")
            self._set_status(f"再生中: {os.path.basename(midi)}  | drv={self.audio_driver.get()}  gain={self.gain.get():.2f}")
            self.root.after(300, self._poll_process)
        except FileNotFoundError:
            messagebox.showerror("fluidsynth が見つかりません", "PATH を通すか、[fluidsynth.exe] で実行ファイルを指定してください。")
        except Exception as e:
            messagebox.showerror("起動エラー", str(e))

    def _ensure_midi_selected(self):
        p = self.selected_midi_path
        if p and os.path.exists(p):
            return True
        midi = filedialog.askopenfilename(
            title="MIDI ファイルを選択",
            filetypes=[("MIDI", "*.mid *.midi")],
            initialdir=self.last_midi_dir
        )
        if not midi:
            return False
        self.selected_midi_path = midi
        self.last_midi_dir = os.path.dirname(midi)
        self.cfg["last_midi_dir"] = self.last_midi_dir
        save_config(self.cfg)
        self.midi_label.config(text=self._short(midi))
        return True

    def pause(self):
        if not (self.proc and self.running) or self.paused:
            return
        try:
            if os.name == "nt":
                ps = psutil.Process(self.proc.pid); ps.suspend()
            else:
                os.kill(self.proc.pid, signal.SIGSTOP)
            self.paused = True
            self._apply_state("paused")
            self._set_status("一時停止中")
        except Exception as e:
            messagebox.showerror("一時停止エラー", str(e))

    def resume(self):
        if not (self.proc and self.running) or not self.paused:
            return
        try:
            if os.name == "nt":
                ps = psutil.Process(self.proc.pid); ps.resume()
            else:
                os.kill(self.proc.pid, signal.SIGCONT)
            self.paused = False
            self._apply_state("playing")
            self._set_status("再生再開")
        except Exception as e:
            messagebox.showerror("再開エラー", str(e))

    def wait_until_finish(self):
        if self.proc and self.running:
            self._set_status("終了待ち...")
            try:
                self.proc.wait()
            except Exception:
                pass
            self.running = False
            self.paused = False
            self.proc = None
            self._apply_state("stopped")
            self._set_status("停止/終了")

    def stop(self):
        if self.proc:
            try:
                if self.paused:
                    try:
                        if os.name == "nt":
                            ps = psutil.Process(self.proc.pid); ps.resume()
                        else:
                            os.kill(self.proc.pid, signal.SIGCONT)
                    except Exception:
                        pass
                if os.name == "nt":
                    self.proc.terminate()
                    for _ in range(20):
                        if self.proc.poll() is not None:
                            break
                        time.sleep(0.05)
                    if self.proc.poll() is None:
                        self.proc.kill()
                else:
                    self.proc.terminate()
            except Exception:
                pass
            finally:
                self.proc = None
        self.running = False
        self.paused = False
        self._apply_state("stopped")
        self._set_status("停止/終了")

    # ---------- Pickers ----------
    def pick_fluidsynth(self):
        p = filedialog.askopenfilename(
            title="fluidsynth 実行ファイルを選択",
            filetypes=[("fluidsynth.exe", "*.exe"), ("すべて", "*.*")],
            initialdir=self.last_fs_dir
        )
        if not p:
            return
        self.fs_exe_path = p
        self.last_fs_dir = os.path.dirname(p)
        self.cfg["fluidsynth"] = p
        self.cfg["last_fs_dir"] = self.last_fs_dir
        save_config(self.cfg)
        self.fs_label.config(text=self._short(self.fs_exe_path))

    def pick_sf2(self):
        p = filedialog.askopenfilename(
            title="SoundFont (.sf2)",
            filetypes=[("SoundFont", "*.sf2")],
            initialdir=self.last_sf2_dir
        )
        if not p:
            return
        self.sf2_path = p
        self.last_sf2_dir = os.path.dirname(p)
        self.cfg["soundfont"] = p
        self.cfg["last_sf2_dir"] = self.last_sf2_dir
        save_config(self.cfg)
        self.sf_label.config(text=self._short(self.sf2_path))

    def pick_midi(self):
        p = filedialog.askopenfilename(
            title="MIDI ファイル",
            filetypes=[("MIDI", "*.mid *.midi")],
            initialdir=self.last_midi_dir
        )
        if p:
            self.selected_midi_path = p
            self.last_midi_dir = os.path.dirname(p)
            self.cfg["last_midi_dir"] = self.last_midi_dir
            save_config(self.cfg)
            self.midi_label.config(text=self._short(p))
            # 選択直後にメタだけ先に出す（midoがあれば）
            if _HAVE_MIDO:
                try:
                    meta = extract_meta(p)
                    self.song_meta.config(
                        text=f"Tempo: {meta['bpm']} BPM  |  TS: {meta['time_sig']}  |  Key: {meta['key']}"
                             + (f"  (+{meta['tempo_changes']} tempo changes)" if meta['tempo_changes'] else "")
                    )
                except Exception:
                    pass

    # ---------- State / persist ----------
    def _apply_state(self, mode):
        if mode == "stopped":
            self.btn_play.config(state="normal")
            self.btn_pause.config(state="disabled")
            self.btn_resume.config(state="disabled")
            self.btn_stop.config(state="disabled")
            self.btn_wait.config(state="disabled")
        elif mode == "playing":
            self.btn_play.config(state="disabled")
            self.btn_pause.config(state="normal")
            self.btn_resume.config(state="disabled")
            self.btn_stop.config(state="normal")
            self.btn_wait.config(state="normal")
        elif mode == "paused":
            self.btn_play.config(state="disabled")
            self.btn_pause.config(state="disabled")
            self.btn_resume.config(state="normal")
            self.btn_stop.config(state="normal")
            self.btn_wait.config(state="normal")

    def _persist_controls(self):
        self.cfg["audio_driver"] = self.audio_driver.get()
        self.cfg["gain"] = round(float(self.gain.get()), 2)
        save_config(self.cfg)

    def _on_gain_change(self, *_):
        try:
            val = float(self.gain_scale.get())
        except Exception:
            val = float(self.gain.get())
        self.gain.set(val)
        self.gain_value.config(text=f"{val:.2f}")
        self._persist_controls()

    def _toggle_pause_key(self, event):
        if self.running and not self.paused:
            self.pause()
        elif self.running and self.paused:
            self.resume()

    def _set_status(self, text):
        self.status.config(text=text)

    # ---------- Cleanup ----------
    def clear_memory(self):
        self.cfg = {}
        try:
            with open(config_path(), "w", encoding="utf-8") as f:
                f.write("{}")
        except Exception:
            pass
        self.sf2_path = None
        self.fs_exe_path = None
        self.audio_driver.set(DRV_DEFAULT())
        self.gain.set(0.8)
        self.dark.set(False)
        self.selected_midi_path = None
        self.fs_label.config(text="PATH を使用")
        self.sf_label.config(text="未選択")
        self.midi_label.config(text="未選択")
        self.song_meta.config(text="Tempo: -  |  TS: -  |  Key: -")
        self._apply_dark_mode_colors()
        self._set_status("設定をクリアしました")

    def on_close(self):
        self.stop()
        self.root.destroy()

def DRV_DEFAULT():
    return "dsound"  # Windows既定

# ---------- Instrument extraction helper (using mido) ----------
def extract_instruments(midi_path):
    """
    Returns dict: {channel(int 1-16): (bank(int), program(int 0-127), name(str))}
    - Channel 10 -> Drums (bank=128, program=0, name='Drums (Standard Kit)')
    - For channels without explicit program_change, assume program 0 (Acoustic Grand Piano)
    - Bank select via CC#0 (MSB) and CC#32 (LSB) when present
    """
    mid = mido.MidiFile(midi_path)
    chan_info = {ch: {"bank_msb": 0, "bank_lsb": 0, "program": None} for ch in range(16)}

    for track in mid.tracks:
        for msg in track:
            if msg.type == "control_change":
                ch = msg.channel
                if msg.control == 0:   # Bank Select MSB
                    chan_info[ch]["bank_msb"] = msg.value
                elif msg.control == 32:  # Bank Select LSB
                    chan_info[ch]["bank_lsb"] = msg.value
            elif msg.type == "program_change":
                ch = msg.channel
                if chan_info[ch]["program"] is None:
                    chan_info[ch]["program"] = msg.program

    used = {}
    for ch in range(16):
        disp_ch = ch + 1  # human-friendly
        if disp_ch == 10:
            used[disp_ch] = (128, 0, "Drums (Standard Kit)")
            continue
        pg = chan_info[ch]["program"]
        bank = chan_info[ch]["bank_msb"] * 128 + chan_info[ch]["bank_lsb"]
        if pg is None:
            pg = 0  # default piano when no program change
        name = GM_PROGRAMS[pg] if 0 <= pg < 128 else f"Program {pg}"
        used[disp_ch] = (bank, pg, name)
    return used

# ---------- Tempo/Key extraction helper (using mido) ----------
def extract_meta(midi_path):
    """
    Returns dict with: bpm (float), time_sig "N/D", key (str),
    and counts of changes (tempo_changes, key_changes, ts_changes).
    """
    mid = mido.MidiFile(midi_path)
    tempos = []      # (abs_ticks, tempo_us_per_quarter)
    time_sigs = []   # (abs_ticks, (nn, dd))
    keys = []        # (abs_ticks, key_text)

    for track in mid.tracks:
        abs_ticks = 0
        for msg in track:
            abs_ticks += msg.time
            if msg.type == "set_tempo":
                tempos.append((abs_ticks, msg.tempo))
            elif msg.type == "time_signature":
                time_sigs.append((abs_ticks, (msg.numerator, msg.denominator)))
            elif msg.type == "key_signature":
                keys.append((abs_ticks, msg.key))

    # 初期値
    bpm_init = 120.0
    if tempos:
        try:
            bpm_init = 60000000.0 / tempos[0][1]
        except Exception:
            bpm_init = 120.0

    ts_init = (4, 4)
    if time_sigs:
        ts_init = time_sigs[0][1]

    key_init = "不明"
    if keys:
        k = keys[0][1]
        # 例: 'C', 'G', 'a', 'f# minor' 等 → 見やすく
        key_init = normalize_key_text(k)

    return {
        "bpm": round(bpm_init, 2),
        "time_sig": f"{ts_init[0]}/{ts_init[1]}",
        "key": key_init,
        "tempo_changes": max(0, len(tempos) - 1),
        "key_changes": max(0, len(keys) - 1),
        "ts_changes": max(0, len(time_sigs) - 1),
    }

def normalize_key_text(k: str) -> str:
    """midoのkey文字列を 'C major' / 'A minor' 形式に寄せる軽い整形。"""
    if not k:
        return "不明"
    # midoは短調を小文字で返すことが多い（例: 'a'）
    # ここでは簡易変換：小文字のみ→ minor、その他→ major として扱う
    # 例外的な 'f#' 等はそのままシャープ/フラット表記
    if k.islower():  # 'a', 'c#', 'f' ...
        return k.upper() + " minor"
    # すでに "X minor"/"X major" 形式のときはタイトルケースに
    k2 = k.title()
    if "Minor" in k2 or "Major" in k2:
        return k2
    return k2 + " major"

def DRV_DEFAULT():
    return "dsound"  # Windows既定

if __name__ == "__main__":
    root = tk.Tk()
    app = SimpleMIDIPlayer200Design(root)
    root.mainloop()
