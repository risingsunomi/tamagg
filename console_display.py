import tkinter as tk
from tkinter.scrolledtext import ScrolledText

class ConsoleDisplay:
    def __init__(self, root):
        self.root = root
        self.text_widget = ScrolledText(root, wrap=tk.WORD, bg="black", fg="lime", font=("Consolas", 12), insertbackground="lime")
        self.text_widget.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.shared_buffer = []
        
        # Configure grid to make the text widget resizable
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

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
