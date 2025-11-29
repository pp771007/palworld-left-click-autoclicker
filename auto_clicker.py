import tkinter as tk
from tkinter import ttk
import threading
import json
import os
import win32api
import win32con
from pynput import keyboard

# --- 設定檔路徑 ---
CONFIG_FILE = "config.json"

# --- 預設設定 ---
DEFAULT_CONFIG = {
    "trigger_key": "F2",   # 觸發連點的熱鍵
    "click_count": 10      # 連點次數
}

class AutoClickerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("《帕魯》右鍵連點")
        self.root.geometry("280x160")
        self.root.resizable(False, False)

        # 核心變數
        self.is_running = True  # 預設為：開啟偵測
        self.click_lock = threading.Lock()
        
        # 載入設定
        self.config = self.load_config()

        # UI 變數
        self.var_trigger_key = tk.StringVar(value=self.config["trigger_key"])
        self.var_count = tk.StringVar(value=str(self.config["click_count"]))
        self.btn_text = tk.StringVar(value="偵測中... (點擊停止)")

        # 建立 UI
        self.create_widgets()

        # 啟動鍵盤監聽
        self.listener = keyboard.Listener(on_press=self.on_key_press)
        self.listener.start()

        # 綁定變數變更以自動儲存
        self.var_trigger_key.trace_add("write", self.auto_save)
        self.var_count.trace_add("write", self.auto_save)

        # 處理視窗關閉
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                loaded = json.load(f)
                # 合併預設值，防止舊版 config 缺漏
                return {**DEFAULT_CONFIG, **loaded}
            except:
                pass
        return DEFAULT_CONFIG

    def auto_save(self, *args):
        try:
            count = int(self.var_count.get())
            if count < 1: count = 1
            if count > 100: count = 100
        except ValueError:
            count = 10 

        data = {
            "trigger_key": self.var_trigger_key.get(),
            "click_count": count
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f, indent=4)

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 1. 狀態/開關按鈕
        self.btn_toggle = tk.Button(
            main_frame, 
            textvariable=self.btn_text, 
            command=self.toggle_running,
            font=("Arial", 12, "bold"),
            bg="#90ee90", # 預設開啟，所以是淺綠色
            height=2
        )
        self.btn_toggle.pack(fill=tk.X, pady=(0, 15))

        # 2. 觸發熱鍵設定
        frame_hotkey = ttk.Frame(main_frame)
        frame_hotkey.pack(fill=tk.X, pady=5)
        ttk.Label(frame_hotkey, text="熱鍵:").pack(side=tk.LEFT)
        
        hotkeys = [f"F{i}" for i in range(1, 13)]
        self.combo_hotkey = ttk.Combobox(frame_hotkey, textvariable=self.var_trigger_key, values=hotkeys, state="readonly", width=8)
        self.combo_hotkey.pack(side=tk.RIGHT)

        # 3. 連點次數設定
        frame_count = ttk.Frame(main_frame)
        frame_count.pack(fill=tk.X, pady=5)
        ttk.Label(frame_count, text="次數 (1-100):").pack(side=tk.LEFT)
        
        # 限制範圍 1-100
        spin_count = ttk.Spinbox(frame_count, from_=1, to=100, textvariable=self.var_count, width=8)
        spin_count.pack(side=tk.RIGHT)

    def toggle_running(self):
        """切換總開關"""
        self.is_running = not self.is_running
        if self.is_running:
            self.btn_text.set("偵測中... (點擊停止)")
            self.btn_toggle.config(bg="#90ee90") # 淺綠色
            self.combo_hotkey.config(state="disabled") # 執行時鎖定熱鍵選單
        else:
            self.btn_text.set("已暫停 (點擊啟動)")
            self.btn_toggle.config(bg="#dddddd") # 灰色
            self.combo_hotkey.config(state="readonly")

    def perform_burst_clicks(self):
        """執行高速連點邏輯"""
        if not self.click_lock.acquire(blocking=False):
            return

        try:
            try:
                count = int(self.var_count.get())
                # 這裡再次確保範圍，防止手動輸入超規數字
                count = max(1, min(100, count))
            except:
                count = 10
            
            # 高速執行 Loop
            for _ in range(count):
                win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
                win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)

        finally:
            self.click_lock.release()

    def on_key_press(self, key):
        """鍵盤監聽回呼"""
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
        if self.listener:
            self.listener.stop()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = AutoClickerApp(root)
    root.mainloop()