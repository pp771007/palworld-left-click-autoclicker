import tkinter as tk
from tkinter import ttk
import threading
import json
import os
import win32api
import win32con
from pynput import keyboard

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "trigger_key": "F2",
    "click_count": 10,
    "window_x": None,
    "window_y": None
}

class AutoClickerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("右鍵連點器")
        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass
        
        self.config = self.load_config()

        win_w = 260
        win_h = 160
        
        x = self.config.get("window_x")
        y = self.config.get("window_y")

        if x is not None and y is not None:
            self.root.geometry(f"{win_w}x{win_h}+{x}+{y}")
        else:
            self.root.geometry(f"{win_w}x{win_h}")
            
        self.root.resizable(False, False)

        self.is_running = True
        self.click_lock = threading.Lock()

        self.var_trigger_key = tk.StringVar(value=self.config["trigger_key"])
        self.var_count = tk.StringVar(value=str(self.config["click_count"]))
        self.btn_text = tk.StringVar(value="偵測中... (點擊停止)")

        self.create_widgets()

        self.listener = keyboard.Listener(on_press=self.on_key_press)
        self.listener.start()

        self.var_trigger_key.trace_add("write", self.save_config)
        self.var_count.trace_add("write", self.save_config)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    loaded = json.load(f)
                return {**DEFAULT_CONFIG, **loaded}
            except:
                pass
        return DEFAULT_CONFIG

    def save_config(self, *args):
        try:
            count = int(self.var_count.get())
            if count < 1: count = 1
            if count > 100: count = 100
        except ValueError:
            count = 10 

        current_x = self.root.winfo_x()
        current_y = self.root.winfo_y()
        
        if self.root.state() != 'iconic':
            final_x = current_x
            final_y = current_y
        else:
            final_x = self.config.get("window_x")
            final_y = self.config.get("window_y")

        data = {
            "trigger_key": self.var_trigger_key.get(),
            "click_count": count,
            "window_x": final_x,
            "window_y": final_y
        }
        
        self.config = data

        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(data, f, indent=4)
        except Exception:
            pass

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        settings_frame = ttk.LabelFrame(main_frame, text="設定", padding=10)
        settings_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(settings_frame, text="熱鍵:").pack(side=tk.LEFT, padx=(0, 5))
        
        hotkeys = [f"F{i}" for i in range(1, 13)]
        self.combo_hotkey = ttk.Combobox(settings_frame, textvariable=self.var_trigger_key, values=hotkeys, state="readonly", width=4)
        self.combo_hotkey.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(settings_frame, text="次數:").pack(side=tk.LEFT, padx=(0, 5))
        
        spin_count = ttk.Spinbox(settings_frame, from_=1, to=100, textvariable=self.var_count, width=4)
        spin_count.pack(side=tk.LEFT)

        self.btn_toggle = tk.Button(
            main_frame, 
            textvariable=self.btn_text, 
            command=self.toggle_running,
            font=("Arial", 11, "bold"),
            bg="#90ee90",
            height=2
        )
        self.btn_toggle.pack(fill=tk.X)

    def toggle_running(self):
        self.is_running = not self.is_running
        if self.is_running:
            self.btn_text.set("偵測中... (點擊停止)")
            self.btn_toggle.config(bg="#90ee90")
            self.combo_hotkey.config(state="disabled")
        else:
            self.btn_text.set("已暫停 (點擊啟動)")
            self.btn_toggle.config(bg="#dddddd")
            self.combo_hotkey.config(state="readonly")

    def perform_burst_clicks(self):
        if not self.click_lock.acquire(blocking=False):
            return

        try:
            try:
                count = int(self.var_count.get())
                count = max(1, min(100, count))
            except:
                count = 10
            
            for _ in range(count):
                win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
                win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
        finally:
            self.click_lock.release()

    def on_key_press(self, key):
        if not self.is_running:
            return

        try:
            target_key_str = self.var_trigger_key.get()
            if key == keyboard.Key[target_key_str.lower()]:
                t = threading.Thread(target=self.perform_burst_clicks)
                t.daemon = True
                t.start()
        except:
            pass 

    def on_close(self):
        self.save_config()
        if self.listener:
            self.listener.stop()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = AutoClickerApp(root)
    root.mainloop()