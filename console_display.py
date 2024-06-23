import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from datetime import datetime

class ConsoleDisplay:
    def __init__(self, root):
        self.root = root
        self.text_widget = ScrolledText(root, wrap=tk.WORD, bg="black", fg="lime", font=("Consolas", 12), insertbackground="lime")
        self.text_widget.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.shared_buffer = []
        
        # Configure grid to make the text widget resizable
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

    def update_display(self, ftype: str=None):
        while self.shared_buffer:
            text = self.shared_buffer.pop(0)
            
            if ftype == "ai":
                ai_text_widget = ScrolledText(self.root, wrap=tk.WORD, bg="black", fg="lime", font=("Consolas", 12), insertbackground="lime")
                ai_text_widget.configure(bg="black", fg="darkred")
                ai_text_widget.insert(tk.END, text + '\n')
                ai_text_widget.see(tk.END)
            else:
                self.text_widget.insert(tk.END, text + '\n')
                self.text_widget.see(tk.END)

    def add_text(self, text: str, ftype: str=None):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.shared_buffer.append(f"[{timestamp}] {text}")
        self.update_display(ftype)

if __name__ == "__main__":
    root = tk.Tk()
    display = ConsoleDisplay(root)
    root.mainloop()
