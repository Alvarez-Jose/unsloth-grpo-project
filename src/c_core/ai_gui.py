"""
Super Simple AI GUI - Guaranteed to work
"""

import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
import time
import random

class SimpleAIGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AI Assistant")
        self.root.geometry("600x500")
        
        # Make it look nice
        self.root.configure(bg='#f0f0f0')
        
        # Header
        header = tk.Label(
            self.root,
            text="🤖 AI Assistant",
            font=("Arial", 20, "bold"),
            bg='#2c3e50',
            fg='white',
            padx=20,
            pady=10
        )
        header.pack(fill=tk.X)
        
        # Chat area
        self.chat_area = scrolledtext.ScrolledText(
            self.root,
            wrap=tk.WORD,
            font=("Arial", 10),
            bg='white',
            fg='#2c3e50',
            height=15,
            relief=tk.FLAT
        )
        self.chat_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        self.chat_area.config(state=tk.DISABLED)
        
        # Welcome message
        self.add_message("AI", "Hello! I'm your AI assistant. How can I help you today?")
        
        # Input area
        input_frame = tk.Frame(self.root, bg='#f0f0f0')
        input_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.input_field = tk.Entry(
            input_frame,
            font=("Arial", 12),
            relief=tk.FLAT,
            bd=2
        )
        self.input_field.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.input_field.bind("<Return>", self.send_message)
        
        # Send button with hover effect
        self.send_btn = tk.Button(
            input_frame,
            text="Send",
            command=self.send_message,
            bg='#3498db',
            fg='white',
            font=("Arial", 11, "bold"),
            relief=tk.FLAT,
            padx=20,
            cursor="hand2"
        )
        self.send_btn.pack(side=tk.RIGHT)
        
        # Add hover effect
        self.send_btn.bind("<Enter>", lambda e: self.send_btn.configure(bg='#2980b9'))
        self.send_btn.bind("<Leave>", lambda e: self.send_btn.configure(bg='#3498db'))
        
        # Quick buttons frame
        buttons_frame = tk.Frame(self.root, bg='#f0f0f0')
        buttons_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Quick action buttons
        quick_actions = [
            ("🐛 Debug Help", "Help me debug this error"),
            ("📁 Find Files", "Find all Python files"),
            ("📊 System Info", "Show system information"),
            ("🧹 Clear Chat", self.clear_chat),
        ]
        
        for i, (text, action) in enumerate(quick_actions):
            if callable(action):
                btn = tk.Button(
                    buttons_frame,
                    text=text,
                    command=action,
                    bg='#95a5a6',
                    fg='white',
                    relief=tk.FLAT,
                    padx=10,
                    cursor="hand2"
                )
            else:
                btn = tk.Button(
                    buttons_frame,
                    text=text,
                    command=lambda a=action: self.quick_action(a),
                    bg='#2ecc71',
                    fg='white',
                    relief=tk.FLAT,
                    padx=10,
                    cursor="hand2"
                )
            btn.grid(row=0, column=i, padx=2, sticky="ew")
            buttons_frame.columnconfigure(i, weight=1)
            
            # Add hover effect
            btn.bind("<Enter>", lambda e, b=btn: b.configure(bg='#7f8c8d' if b.cget('bg') == '#95a5a6' else '#27ae60'))
            btn.bind("<Leave>", lambda e, b=btn: b.configure(bg='#95a5a6' if b.cget('bg') == '#7f8c8d' else '#2ecc71'))
    
    def quick_action(self, action_text):
        """Handle quick action button click"""
        self.input_field.delete(0, tk.END)
        self.input_field.insert(0, action_text)
        self.send_message()
    
    def add_message(self, sender, message):
        """Add message to chat area"""
        self.chat_area.config(state=tk.NORMAL)
        
        # Color code sender
        if sender == "You":
            self.chat_area.insert(tk.END, f"{sender}: ", "user")
        elif sender == "AI":
            self.chat_area.insert(tk.END, f"{sender}: ", "ai")
        else:
            self.chat_area.insert(tk.END, f"{sender}: ")
        
        self.chat_area.insert(tk.END, f"{message}\n\n")
        self.chat_area.config(state=tk.DISABLED)
        self.chat_area.see(tk.END)
        
        # Configure tags
        self.chat_area.tag_config("user", foreground="#3498db", font=("Arial", 10, "bold"))
        self.chat_area.tag_config("ai", foreground="#2ecc71", font=("Arial", 10, "bold"))
    
    def send_message(self, event=None):
        """Send user message"""
        message = self.input_field.get().strip()
        if not message:
            return
        
        # Clear input
        self.input_field.delete(0, tk.END)
        
        # Add user message
        self.add_message("You", message)
        
        # Disable send button while processing
        self.send_btn.config(state=tk.DISABLED, text="Thinking...")
        
        # Process in background
        threading.Thread(target=self.get_ai_response, args=(message,), daemon=True).start()
    
    def get_ai_response(self, message):
        """Get AI response (simulated)"""
        # Simulate thinking time
        time.sleep(1)
        
        # AI responses based on message content
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['debug', 'error', 'crash', 'bug']):
            responses = [
                f"Let me help you debug that issue. '{message}' sounds like a common problem.",
                "I'll analyze that error for you. Can you provide more details about the crash?",
                "For debugging issues, try checking the logs first. What error message are you seeing?",
            ]
        elif any(word in message_lower for word in ['file', 'find', 'search', 'locate']):
            responses = [
                "I can help you find files. What specific files are you looking for?",
                "For file searches, I recommend checking your project structure first.",
                f"Looking for files related to: '{message}'. Should I search recursively?",
            ]
        elif any(word in message_lower for word in ['system', 'info', 'stat']):
            responses = [
                "Here's some system information...",
                "Checking system status...",
                "I'll gather system information for you.",
            ]
        else:
            responses = [
                f"I understand you're asking about: '{message}'",
                f"Interesting question: '{message}'. Let me think about that...",
                f"Processing your query: '{message}'",
                f"Based on '{message}', here's what I think...",
            ]
        
        response = random.choice(responses)
        
        # Update GUI
        self.root.after(0, lambda: self.add_message("AI", response))
        self.root.after(0, lambda: self.send_btn.config(state=tk.NORMAL, text="Send"))
    
    def clear_chat(self):
        """Clear chat history"""
        if messagebox.askyesno("Clear Chat", "Clear all messages?"):
            self.chat_area.config(state=tk.NORMAL)
            self.chat_area.delete("1.0", tk.END)
            self.chat_area.config(state=tk.DISABLED)
            self.add_message("AI", "Chat cleared. How can I help you?")
    
    def run(self):
        """Run the GUI"""
        self.root.mainloop()

if __name__ == "__main__":
    gui = SimpleAIGUI()
    gui.run()