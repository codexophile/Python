import tkinter as tk

class Widget(tk.Tk):
    def __init__(self):
        super().__init__()
        self.overrideredirect(True)
        # self.attributes('-topmost', True)
        self.attributes('-alpha', 0.8)
        self.geometry('200x100+100+100')
        self.label = tk.Label(self, text="Hello, World!")
        self.label.pack()
        self.bind('<ButtonPress-1>', self.start_move)
        self.bind('<ButtonRelease-1>', self.stop_move)
        self.bind('<B1-Motion>', self.do_move)

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def stop_move(self, event):
        self.x = None
        self.y = None

    def do_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.winfo_x() + deltax
        y = self.winfo_y() + deltay
        self.geometry(f"+{x}+{y}")

if __name__ == "__main__":
    widget = Widget()
    widget.mainloop()