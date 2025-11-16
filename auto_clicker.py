import win32api
import win32con
import threading
from pynput import mouse
import time

# 我們需要一個鎖 (Lock) 來防止腳本觸發自己，造成無限循環。
# 這是最關鍵的部分。
click_lock = threading.Lock()

# 定義連點的次數
CLICK_COUNT = 10

def perform_ten_clicks():
    """
    使用 win32api 執行 10 次高速右鍵點擊。
    這是 Windows 上最快的方法。
    """
    # 嘗試獲取鎖。如果鎖已被其他執行緒佔用（代表正在連點中），
    # 則 acquire 會返回 False，我們就直接結束，避免重複觸發。
    # blocking=False 讓它不會卡住，而是立即返回結果。
    if not click_lock.acquire(blocking=False):
        return

    try:
        # 在這裡執行你的高速點擊邏輯
        for _ in range(CLICK_COUNT):
            win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
            win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
            # 注意：這裡不加 time.sleep() 以達到最高速度

    finally:
        # 點擊完成後，無論如何都必須釋放鎖，以便下次可以正常觸發。
        # 使用 finally 確保即使發生錯誤，鎖也會被釋放。
        click_lock.release()

def on_click(x, y, button, pressed):
    """
    這是 pynput 的回呼函數，當有滑鼠事件時會被調用。
    """
    # 我們只關心「右鍵」被「按下」的那個瞬間
    if button == mouse.Button.right and pressed:
        # 當偵測到使用者按下右鍵時，
        # 啟動一個新的執行緒 (thread) 去執行我們的連點函數。
        # 這樣做可以避免阻塞主監聽執行緒，讓程式反應更靈敏。
        click_thread = threading.Thread(target=perform_ten_clicks)
        click_thread.start()

# --- 主程式開始 ---
print("腳本已啟動：點擊一次右鍵將觸發 10 次高速連擊。")
print("若要停止腳本，請關閉此視窗。")

# 創建一個滑鼠監聽器
# 使用 'with' 語法可以確保程式結束時監聽器會被妥善地關閉
with mouse.Listener(on_click=on_click) as listener:
    # 讓監聽器持續運行
    listener.join()

print("腳本已停止。")