import tkinter as tk
from tkinter import scrolledtext, ttk
import threading
import asyncio
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

class AIGUI:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Project Cortex AI Assistant")
        self.window.geometry("800x600")
        
        self.setup_gui()
        
    def setup_gui(self):
        # Header
        header = tk.Label(
            self.window, 
            text="🤖 Project Cortex AI Assistant", 
            font=("Arial", 16, "bold")
        )
        header.pack(pady=10)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = tk.Label(
            self.window, 
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Chat display
        self.chat_display = scrolledtext.ScrolledText(
            self.window,
            wrap=tk.WORD,
            width=80,
            height=20,
            font=("Consolas", 10)
        )
        self.chat_display.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        self.chat_display.config(state=tk.DISABLED)
        
        # Input area
        input_frame = tk.Frame(self.window)
        input_frame.pack(pady=10, padx=10, fill=tk.X)
        
        self.user_input = tk.Entry(input_frame, font=("Arial", 12))
        self.user_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.user_input.bind("<Return>", self.send_message)
        
        send_btn = tk.Button(
            input_frame,
            text="Send",
            command=self.send_message,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 10, "bold")
        )
        send_btn.pack(side=tk.RIGHT)
        
        # Control buttons
        control_frame = tk.Frame(self.window)
        control_frame.pack(pady=5)
        
        buttons = [
            ("Start Monitoring", self.start_monitoring, "#2196F3"),
            ("Stop Monitoring", self.stop_monitoring, "#f44336"),
            ("Clear Chat", self.clear_chat, "#FF9800"),
            ("Export Logs", self.export_logs, "#9C27B0"),
        ]
        
        for text, command, color in buttons:
            btn = tk.Button(
                control_frame,
                text=text,
                command=command,
                bg=color,
                fg="white",
                padx=10,
                pady=5
            )
            btn.pack(side=tk.LEFT, padx=5)
    
    def add_message(self, sender, message, color="black"):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"{sender}: ", "bold")
        self.chat_display.insert(tk.END, f"{message}\n\n")
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)
        
        # Apply tags for formatting
        self.chat_display.tag_config("bold", font=("Arial", 10, "bold"))
        self.chat_display.tag_config("user", foreground="blue")
        self.chat_display.tag_config("ai", foreground="green")
    
    def send_message(self, event=None):
        message = self.user_input.get().strip()
        if not message:
            return
        
        self.add_message("You", message, "blue")
        self.user_input.delete(0, tk.END)
        
        # Process message in background
        threading.Thread(target=self.process_ai_response, args=(message,)).start()
    
    def process_ai_response(self, message):
        self.status_var.set("🤔 AI thinking...")
        
        # Simulate AI processing
        import time
        import random
        
        time.sleep(1)  # Simulate processing time
        
        responses = [
            f"I understand you're asking about: {message}",
            f"Processing your request: {message}",
            f"Based on my analysis of '{message}', here's what I found...",
            f"Query received: {message}. Searching for relevant information...",
        ]
        
        response = random.choice(responses)
        
        # Update GUI from main thread
        self.window.after(0, lambda: self.add_message("AI Assistant", response, "green"))
        self.window.after(0, lambda: self.status_var.set("Ready"))
    
    def start_monitoring(self):
        self.status_var.set("📡 Starting system monitoring...")
        self.add_message("System", "Starting ETW monitoring...")
    
    def stop_monitoring(self):
        self.status_var.set("Stopping monitoring...")
        self.add_message("System", "Stopping all monitoring services")
    
    def clear_chat(self):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete(1.0, tk.END)
        self.chat_display.config(state=tk.DISABLED)
        self.add_message("System", "Chat cleared")
    
    def export_logs(self):
        self.status_var.set("Exporting logs...")
        self.add_message("System", "Exporting conversation logs to file")
    
    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    gui = AIGUI()
    gui.run()