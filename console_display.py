import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from datetime import datetime

class ConsoleDisplay:
    def __init__(self, root):
        self.root = root
        self.text_widget = ScrolledText(root, wrap=tk.WORD, bg="black", font=("Consolas", 12), insertbackground="lime")
        self.text_widget.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # Configure grid to make the text widget resizable
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Set up tag configurations for different text types
        self.text_widget.tag_configure("system", foreground="lime")
        self.text_widget.tag_configure("ai", foreground="darkred")
        self.text_widget.tag_configure("user", foreground="white")

        self.shared_buffer = []

    def update_display(self, ftype: str):
        while self.shared_buffer:
            text = self.shared_buffer.pop(0)
            self.text_widget.insert(tk.END, text, ftype)
            self.text_widget.see(tk.END)

    def add_text(self, text: str, ftype: str="system"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.shared_buffer.append(f"{timestamp} [{ftype.upper()}] {text}\n")
        self.update_display(ftype)

if __name__ == "__main__":
    root = tk.Tk()
    display = ConsoleDisplay(root)
    root.mainloop()
