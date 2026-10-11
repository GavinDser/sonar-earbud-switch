"""屏幕左上角的小提示（被吞掉的音量键不会再有 Windows 自带的音量框）。"""
import queue
import threading


class Osd:
    def __init__(self, x, y, duration):
        self.x, self.y, self.duration_ms = x, y, int(duration * 1000)
        self.q = queue.Queue()

    def start(self):
        threading.Thread(target=self._loop, daemon=True).start()

    def show(self, text):
        self.q.put(text)

    def _loop(self):
        import tkinter as tk  # 所有 Tk 调用都留在这个线程

        root = tk.Tk()
        root.overrideredirect(True)
        root.attributes("-topmost", True)
        root.attributes("-alpha", 0.9)
        root.configure(bg="#202020")
        label = tk.Label(root, font=("Segoe UI", 16), fg="white", bg="#202020", padx=20, pady=10)
        label.pack()
        root.withdraw()
        hide_job = None

        def poll():
            nonlocal hide_job
            text = None
            while not self.q.empty():
                text = self.q.get_nowait()
            if text is not None:
                label.config(text=text)
                root.update_idletasks()
                root.geometry(f"+{self.x}+{self.y}")
                root.deiconify()
                root.lift()
                if hide_job:
                    root.after_cancel(hide_job)
                hide_job = root.after(self.duration_ms, root.withdraw)
            root.after(50, poll)

        poll()
        root.mainloop()
