import tkinter as tk
from tkinter.scrolledtext import ScrolledText

class ConsoleDisplay:
    def __init__(self, root):
        self.root = root
        self.root.title("Console Display")
        self.text_widget = ScrolledText(root, wrap=tk.WORD, width=50, height=15, bg="black", fg="lime", font=("Consolas", 12), insertbackground="lime")
        self.text_widget.pack(pady=20)
        self.shared_buffer = []

    def update_display(self):
        while self.shared_buffer:
            text = self.shared_buffer.pop(0)
            self.text_widget.insert(tk.END, text + '\n')
            self.text_widget.see(tk.END)

    def add_text(self, text):
        self.shared_buffer.append(text)
        self.update_display()

if __name__ == "__main__":
    root = tk.Tk()
    display = ConsoleDisplay(root)
    root.mainloop()
