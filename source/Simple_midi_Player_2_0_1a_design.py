
import os
import json
import time
import signal
import psutil
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk

APP_TITLE = "Simple MIDI Player v2.0.1 (Design Refresh)"
CONFIG_NAME = "mhp_config.json"
DRIVER_CHOICES = ["dsound", "wasapi", "portaudio"]

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
        x, y, cx, cy = self.widget.bbox("insert") or (0,0,0,0)
        x += self.widget.winfo_rootx() + 20
        y += self.widget.winfo_rooty() + 25
        self.tip = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        lbl = ttk.Label(tw, text=self.text, padding=(8,4))
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
        self.root.geometry("920x540")
        self.root.minsize(820, 460)
        self.proc = None
        self.running = False
        self.paused = False

        # Load config
        self.cfg = load_config()
        self.sf2_path = self.cfg.get("soundfont")
        self.fs_exe_path = self.cfg.get("fluidsynth")
        self.audio_driver = tk.StringVar(value=self.cfg.get("audio_driver") or DRIVER_CHOICES[0])
        self.gain = tk.DoubleVar(value=float(self.cfg.get("gain", 0.8)))

        self.last_midi_dir = self.cfg.get("last_midi_dir") or os.getcwd()
        self.last_sf2_dir = self.cfg.get("last_sf2_dir") or os.getcwd()
        self.last_fs_dir = self.cfg.get("last_fs_dir") or os.getcwd()

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
            # Use native theme on Windows
            if "vista" in self.style.theme_names():
                self.style.theme_use("vista")
        except Exception:
            pass

        # Base paddings
        self.style.configure("TFrame", padding=6)
        self.style.configure("Card.TFrame", relief="groove", borderwidth=1, padding=12)
        self.style.configure("Title.TLabel", font=("-size", 14, "-weight", "bold"))
        self.style.configure("Status.TLabel", anchor="w")

        # Dark mode colors
        self.dark = tk.BooleanVar(value=bool(self.cfg.get("dark_mode", False)))
        self._apply_dark_mode_colors()

    def _apply_dark_mode_colors(self):
        dark = self.dark.get()
        if dark:
            bg = "#1f2329"
            fg = "#e6e6e6"
            card = "#2a2f36"
            acc = "#3a3f46"
        else:
            bg = "#f7f7fa"
            fg = "#222222"
            card = "#ffffff"
            acc = "#f0f0f5"

        self.root.configure(bg=bg)
        self.style.configure(".", background=bg, foreground=fg)
        self.style.configure("TFrame", background=bg)
        self.style.configure("Card.TFrame", background=card)
        self.style.configure("TLabel", background=bg, foreground=fg)
        self.style.configure("Title.TLabel", background=bg, foreground=fg)
        self.style.configure("TLabelframe", background=bg, foreground=fg)
        self.style.configure("TLabelframe.Label", background=bg, foreground=fg)
        self.style.configure("TButton", padding=(10,4))
        self.style.map("TButton", background=[("active", acc)])

    # ---------- UI ----------
    def _build_ui(self):
        # Header
        header = ttk.Frame(self.root, style="TFrame")
        header.pack(fill="x")
        ttk.Label(header, text="🎧 Simple MIDI Player", style="Title.TLabel").pack(side="left")
        ttk.Button(header, text="🌗 ダークモード", command=self.toggle_dark).pack(side="right")

        # Top cards
        cards = ttk.Frame(self.root)
        cards.pack(fill="x", padx=10, pady=8)

        # Card: Paths
        path_card = ttk.Frame(cards, style="Card.TFrame")
        path_card.pack(side="left", fill="both", expand=True, padx=(0,8))

        row = ttk.Frame(path_card)
        row.pack(fill="x", pady=2)
        b = ttk.Button(row, text="🧰 fluidsynth.exe", command=self.pick_fluidsynth)
        b.pack(side="left")
        Tooltip(b, "fluidsynth実行ファイルを選択")
        self.fs_label = ttk.Label(row, text=self._short(self.fs_exe_path) or "PATH を使用")
        self.fs_label.pack(side="left", padx=10)

        row = ttk.Frame(path_card)
        row.pack(fill="x", pady=2)
        b = ttk.Button(row, text="🎹 SoundFont", command=self.pick_sf2)
        b.pack(side="left")
        Tooltip(b, "SoundFont(.sf2) を選択")
        self.sf_label = ttk.Label(row, text=self._short(self.sf2_path) or "未選択")
        self.sf_label.pack(side="left", padx=10)

        row = ttk.Frame(path_card)
        row.pack(fill="x", pady=2)
        b = ttk.Button(row, text="🎵 MIDI を選択 (Ctrl+O)", command=self.pick_midi)
        b.pack(side="left")
        Tooltip(b, "再生したいMIDIファイルを選択")
        self.midi_label = ttk.Label(row, text="未選択")
        self.midi_label.pack(side="left", padx=10)

        # Card: Settings
        set_card = ttk.Frame(cards, style="Card.TFrame")
        set_card.pack(side="left", fill="y", padx=(8,0))

        r = ttk.Frame(set_card)
        r.pack(fill="x", pady=4)
        ttk.Label(r, text="Audio Driver").pack(side="left")
        self.driver_cmb = ttk.Combobox(r, values=DRIVER_CHOICES, textvariable=self.audio_driver, width=12, state="readonly")
        self.driver_cmb.pack(side="left", padx=6)
        self.driver_cmb.bind("<<ComboboxSelected>>", lambda e: self._persist_controls())

        r = ttk.Frame(set_card)
        r.pack(fill="x", pady=4)
        ttk.Label(r, text="Gain").pack(side="left")
        self.gain_scale = ttk.Scale(r, from_=0.2, to=1.2, value=self.gain.get(), command=self._on_gain_change, length=180)
        self.gain_scale.pack(side="left", padx=6)
        self.gain_value = ttk.Label(r, text=f"{self.gain.get():.2f}")
        self.gain_value.pack(side="left")

        # Controls card
        ctrl_card = ttk.Frame(self.root, style="Card.TFrame")
        ctrl_card.pack(fill="x", padx=10, pady=(0,8))

        self.btn_play = ttk.Button(ctrl_card, text="▶ 再生", command=self.start, width=12)
        self.btn_pause = ttk.Button(ctrl_card, text="⏸ 一時停止", command=self.pause, width=12)
        self.btn_resume = ttk.Button(ctrl_card, text="⏵ 再開", command=self.resume, width=12)
        self.btn_stop = ttk.Button(ctrl_card, text="⏹ 停止", command=self.stop, width=12)
        self.btn_wait = ttk.Button(ctrl_card, text="⌛ 終了待ち", command=self.wait_until_finish, width=12)
        for w in (self.btn_play, self.btn_pause, self.btn_resume, self.btn_stop, self.btn_wait):
            w.pack(side="left", padx=6, pady=4)

        # Log/status area
        bottom = ttk.Frame(self.root, style="Card.TFrame")
        bottom.pack(fill="both", expand=True, padx=10, pady=(0,10))

        # (Design refresh: simple text log replaced by compact status only.
        # If you want a scrolled log later, we can add it back.)
        self.status = ttk.Label(bottom, text="待機中", style="Status.TLabel")
        self.status.pack(fill="x")

        # Footer actions
        foot = ttk.Frame(self.root)
        foot.pack(fill="x", padx=10, pady=(0,10))
        ttk.Button(foot, text="🧽 設定クリア", command=self.clear_memory).pack(side="left")

    def _short(self, path, maxlen=40):
        if not path:
            return ""
        p = os.path.abspath(path)
        return (p if len(p) <= maxlen else ("…" + p[-maxlen:]))

    def toggle_dark(self):
        self.dark.set(not self.dark.get())
        self.cfg["dark_mode"] = bool(self.dark.get())
        save_config(self.cfg)
        self._apply_dark_mode_colors()

    # ---------- Mechanics (unchanged from 2.0.0 concept) ----------
    def _build_cmd(self, midi_path):
        exe = self.fs_exe_path or "fluidsynth"
        driver = self.audio_driver.get().strip() or "dsound"
        gain = float(self.gain.get())
        sf2 = self.sf2_path

        if not sf2 or not os.path.exists(sf2):
            raise FileNotFoundError("SoundFont(.sf2) が未選択、または見つかりません。")
        if not midi_path or not os.path.exists(midi_path):
            raise FileNotFoundError("MIDI ファイルが見つかりません。")

        # 2.0.0の方針：最小限の引数のみ
        cmd = [exe, "-a", driver, "-g", f"{gain:.2f}", "-ni", sf2, midi_path]
        return cmd

    def start(self):
        if self.proc:
            self.stop()
        midi = filedialog.askopenfilename(
            title="MIDI ファイル",
            filetypes=[("MIDI", "*.mid *.midi")],
            initialdir=self.last_midi_dir
        )
        if not midi:
            return
        self.last_midi_dir = os.path.dirname(midi)
        self.cfg["last_midi_dir"] = self.last_midi_dir
        save_config(self.cfg)
        self.midi_label.config(text=self._short(midi))

        try:
            cmd = self._build_cmd(midi)
        except Exception as e:
            messagebox.showerror("起動エラー", str(e))
            return

        try:
            creation = (subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0)
            self.proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                creationflags=creation,
            )
            self.running = True
            self.paused = False
            self._apply_state("playing")
            self._set_status(f"再生中: {os.path.basename(midi)}  | drv={self.audio_driver.get()}  gain={self.gain.get():.2f}")
            # optional watchdog: we just read & ignore to prevent buffer blocking
            self.root.after(200, self._drain_stdout)
        except FileNotFoundError:
            messagebox.showerror("fluidsynth が見つかりません", "PATH を通すか、[fluidsynth.exe] で実行ファイルを指定してください。")
        except Exception as e:
            messagebox.showerror("起動エラー", str(e))

    def _drain_stdout(self):
        if not (self.proc and self.proc.stdout):
            return
        try:
            while True:
                line = self.proc.stdout.readline()
                if not line:
                    break
                # ここではログは表示せず捨てる（UIをシンプルに）。必要ならログ枠を追加して表示できる。
        except Exception:
            pass
        finally:
            if self.proc and self.proc.poll() is None:
                # keep draining
                self.root.after(300, self._drain_stdout)
            else:
                # ended
                self.running = False
                self.paused = False
                self.proc = None
                self._apply_state("stopped")
                self._set_status("停止/終了")

    def pause(self):
        if not (self.proc and self.running) or self.paused:
            return
        try:
            if os.name == "nt":
                ps = psutil.Process(self.proc.pid)
                ps.suspend()
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
                ps = psutil.Process(self.proc.pid)
                ps.resume()
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
            self.proc.wait()
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
                            ps = psutil.Process(self.proc.pid)
                            ps.resume()
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
        # Just update label; actual playback is via [再生] which also asks file.
        p = filedialog.askopenfilename(
            title="MIDI ファイル",
            filetypes=[("MIDI", "*.mid *.midi")],
            initialdir=self.last_midi_dir
        )
        if p:
            self.last_midi_dir = os.path.dirname(p)
            self.cfg["last_midi_dir"] = self.last_midi_dir
            save_config(self.cfg)
            self.midi_label.config(text=self._short(p))

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
        # ttk.Scale doesn't bind variable, so read from widget
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
        # Reset config and UI labels (design-only; mechanics unchanged)
        self.cfg = {}
        try:
            with open(config_path(), "w", encoding="utf-8") as f:
                f.write("{}")
        except Exception:
            pass
        self.sf2_path = None
        self.fs_exe_path = None
        self.audio_driver.set("dsound")
        self.gain.set(0.8)
        self.dark.set(False)
        self.fs_label.config(text="PATH を使用")
        self.sf_label.config(text="未選択")
        self.midi_label.config(text="未選択")
        self._apply_dark_mode_colors()
        self._set_status("設定をクリアしました")


        def on_close(self):
        self.stop()
        self.root.destroy()

if __name__ == "__main__":
    try:
        import tkinter as _tk
    except Exception as e:
        raise SystemExit("Tkinter が利用できません: " + str(e))
    root = tk.Tk()
    app = SimpleMIDIPlayer200Design(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
