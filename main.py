import os
import subprocess
import threading
import random
import tkinter as tk
from datetime import date, datetime
from tkinter import scrolledtext
from dotenv import load_dotenv
from google import genai

# Load environment
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# ---------------- CONFIG & AESTHETICS ----------------
LOG_DIR = "logs"
MODEL_NAME = "gemini-3-flash-preview"

BG_MAIN = "#2E3440"
BG_INPUT = "#3B4252"
FG_TEXT = "#D8DEE9"
ACCENT = "#88C0D0"
SUCCESS = "#A3BE8C"
ERROR = "#BF616A"
HIGHLIGHT = "#EBCB8B"

QUOTES = ["Focus on being productive instead of busy.", "Done is better than perfect.", 
          "Small steps lead to big destinations.", "The only way to go fast is to go well."]

# ---------------- BEAUTIFIED POPUPS ----------------

def custom_popup(title, message, color=ACCENT):
    """Creates an aesthetic Nordic-styled popup window."""
    popup = tk.Toplevel(root)
    popup.title(title)
    popup.geometry("350x180")
    popup.configure(bg=BG_INPUT)
    popup.transient(root)
    popup.grab_set()
    
    # Center the popup relative to root
    x = root.winfo_x() + (root.winfo_width() // 2) - 175
    y = root.winfo_y() + (root.winfo_height() // 2) - 90
    popup.geometry(f"+{x}+{y}")

    tk.Label(popup, text=title.upper(), bg=BG_INPUT, fg=color, 
             font=("Segoe UI", 10, "bold")).pack(pady=(20, 10))
    tk.Label(popup, text=message, bg=BG_INPUT, fg=FG_TEXT, 
             wraplength=300, font=("Segoe UI", 10)).pack(pady=10)
    
    btn = tk.Button(popup, text="DISMISS", command=popup.destroy, bg=BG_MAIN, fg=FG_TEXT,
                    relief="flat", font=("Segoe UI", 9, "bold"), padx=20, pady=5, cursor="hand2")
    btn.pack(pady=15)

# ---------------- LOADING OVERLAY ----------------

loading_overlay = None

def show_loading(message="Working..."):
    global loading_overlay
    loading_overlay = tk.Toplevel(root)
    loading_overlay.overrideredirect(True) # Remove window borders
    loading_overlay.configure(bg=ACCENT)
    
    # Position
    w, h = 250, 80
    x = root.winfo_x() + (root.winfo_width() // 2) - (w // 2)
    y = root.winfo_y() + (root.winfo_height() // 2) - (h // 2)
    loading_overlay.geometry(f"{w}x{h}+{x}+{y}")
    
    inner = tk.Frame(loading_overlay, bg=BG_MAIN)
    inner.pack(padx=2, pady=2, fill="both", expand=True)
    
    tk.Label(inner, text="⏳", font=("Segoe UI", 18), bg=BG_MAIN).pack(pady=(10, 0))
    tk.Label(inner, text=message, fg=FG_TEXT, bg=BG_MAIN, font=("Segoe UI", 10, "bold")).pack()
    root.update_idletasks()

def hide_loading():
    global loading_overlay
    if loading_overlay:
        loading_overlay.destroy()

# ---------------- LOGIC ----------------

def ensure_log_dir():
    if not os.path.exists(LOG_DIR): os.makedirs(LOG_DIR)

def get_today_file():
    today = date.today().isoformat()
    return os.path.join(LOG_DIR, f"{today}.md"), today

def save_log():
    did = did_text.get("1.0", tk.END).strip()
    challenges = challenges_text.get("1.0", tk.END).strip()
    learned = learned_text.get("1.0", tk.END).strip()
    
    if not (did or challenges or learned) or did.startswith("//"):
        custom_popup("Attention", "Please write something before saving. ✨", HIGHLIGHT)
        return

    ensure_log_dir()
    file_path, today = get_today_file()
    now_time = datetime.now().strftime("%I:%M %p")
    
    try:
        with open(file_path, "a", encoding="utf-8") as f:
            if not os.path.exists(file_path): f.write(f"# 📅 Log for {today}\n\n")
            f.write(f"--- \n### 🕒 Entry at {now_time}\n")
            if did: f.write(f"**Progress:**\n{did}\n\n")
            if challenges: f.write(f"**Blockers:**\n{challenges}\n\n")
            if learned: f.write(f"**Learnings:**\n{learned}\n\n")
        
        custom_popup("Success", f"Log entry saved at {now_time} ✅", SUCCESS)
        for txt in [did_text, challenges_text, learned_text]: txt.delete("1.0", tk.END)
    except Exception as e:
        custom_popup("Error", str(e), ERROR)

def generate_summary_thread():
    file_path, _ = get_today_file()
    if not os.path.exists(file_path):
        custom_popup("Missing Log", "Save a log entry first!", HIGHLIGHT)
        return

    show_loading("AI is thinking...")
    
    def run():
        try:
            with open(file_path, "r", encoding="utf-8") as f: content = f.read()
            prompt = f"Summarize this work log into professional bullet points, with exactly 2 sentences for 'Learnings' and 2 sentences for 'Blockers & Risks'.\n\nContent:\n{content}"
            
            response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
            
            # Update UI from main thread
            root.after(0, lambda: summary_box.delete("1.0", tk.END))
            root.after(0, lambda: summary_box.insert(tk.END, response.text.strip()))
        except Exception as e:
            root.after(0, lambda: custom_popup("AI Error", str(e), ERROR))
        finally:
            root.after(0, hide_loading)

    threading.Thread(target=run).start()

def git_commit_thread():
    show_loading("Syncing with GitHub...")
    
    def run():
        try:
            # 1. Stage changes
            subprocess.run(["git", "add", "."], check=True)
            
            # 2. Attempt commit
            # We use capture_output to check what Git says without crashing
            commit_proc = subprocess.run(
                ["git", "commit", "-m", f"Daily log update: {date.today()}"], 
                capture_output=True, 
                text=True
            )
            
            # If returncode is 1, it usually means "nothing to commit"
            if commit_proc.returncode != 0 and "nothing to commit" in commit_proc.stdout:
                root.after(0, lambda: custom_popup("Status", "Everything is already up to date! ✨", HIGHLIGHT))
                return

            # 3. Push changes
            subprocess.run(["git", "push"], check=True, capture_output=True)
            root.after(0, lambda: custom_popup("Git Success", "Pushed to GitHub cloud 🚀", SUCCESS))
            
        except subprocess.CalledProcessError as e:
            # This catches actual errors (like no internet or auth issues)
            error_msg = e.stderr.decode() if e.stderr else "Check Git init status."
            root.after(0, lambda: custom_popup("Git Error", f"Details: {error_msg[:50]}...", ERROR))
        except Exception as e:
            root.after(0, lambda: custom_popup("Error", str(e), ERROR))
        finally:
            root.after(0, hide_loading)

    threading.Thread(target=run).start()

# ---------------- UI CONSTRUCTION (RESPONSIVE) ----------------

root = tk.Tk()
root.title("DeepWork | Minimalist Logger")
root.geometry("800x850")
root.configure(bg=BG_MAIN)

root.grid_columnconfigure(0, weight=1)
root.grid_rowconfigure(0, weight=1)

canvas = tk.Canvas(root, bg=BG_MAIN, highlightthickness=0)
canvas.grid(row=0, column=0, sticky="nsew")

scrollbar = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
scrollbar.grid(row=0, column=1, sticky="ns")

scrollable_frame = tk.Frame(canvas, bg=BG_MAIN)
canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

def on_configure(event):
    canvas.configure(scrollregion=canvas.bbox("all"))
    canvas.itemconfig(canvas_window, width=event.width)

canvas.bind("<Configure>", on_configure)
canvas.configure(yscrollcommand=scrollbar.set)
canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

# ---------------- CONTENT ----------------

def create_styled_section(label_text, height):
    tk.Label(scrollable_frame, text=label_text, bg=BG_MAIN, fg=HIGHLIGHT, font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=40, pady=(20, 5))
    txt = tk.Text(scrollable_frame, height=height, bg=BG_INPUT, fg=FG_TEXT, font=("Consolas", 11), 
                  relief="flat", padx=15, pady=10, insertbackground=FG_TEXT, highlightthickness=1, highlightbackground="#4C566A")
    txt.pack(fill="x", padx=40)
    
    quote = random.choice(QUOTES)
    txt.insert("1.0", f"// {quote}")
    txt.bind("<FocusIn>", lambda e: txt.delete("1.0", tk.END) if txt.get("1.0", tk.END).startswith("//") else None)
    return txt

did_text = create_styled_section("COMPLETED TASKS", 5)
challenges_text = create_styled_section("CHALLENGES / BLOCKERS", 4)
learned_text = create_styled_section("KEY LEARNINGS", 4)

# Buttons
btn_frame = tk.Frame(scrollable_frame, bg=BG_MAIN)
btn_frame.pack(fill="x", padx=40, pady=25)

def mk_btn(parent, text, cmd, color, fg=BG_MAIN):
    return tk.Button(parent, text=text, command=cmd, bg=color, fg=fg, font=("Segoe UI", 9, "bold"), 
                     relief="flat", padx=20, pady=12, cursor="hand2", activebackground=FG_TEXT)

mk_btn(btn_frame, "💾 SAVE ENTRY", save_log, ACCENT).pack(side="left", expand=True, fill="x", padx=5)
mk_btn(btn_frame, "🤖 AI SUMMARIZE", generate_summary_thread, SUCCESS).pack(side="left", expand=True, fill="x", padx=5)

# AI Output
tk.Label(scrollable_frame, text="MANAGER-READY SUMMARY", bg=BG_MAIN, fg=HIGHLIGHT, font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=40, pady=(10, 5))
summary_box = scrolledtext.ScrolledText(scrollable_frame, height=12, bg=BG_INPUT, fg=FG_TEXT, font=("Consolas", 11), relief="flat", padx=15, pady=10)
summary_box.pack(fill="x", padx=40)

# GitHub Button
tk.Label(scrollable_frame, text="VERSION CONTROL", bg=BG_MAIN, fg=HIGHLIGHT, font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=40, pady=(25, 5))
git_btn = mk_btn(scrollable_frame, "🚀 COMMIT & PUSH TO GITHUB", git_commit_thread, BG_MAIN, fg=SUCCESS)
git_btn.config(highlightthickness=1, highlightbackground=SUCCESS)
git_btn.pack(fill="x", padx=40, pady=(0, 50))

root.mainloop()