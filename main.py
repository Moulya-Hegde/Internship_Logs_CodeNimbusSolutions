import os
import subprocess
import threading
import random
import tkinter as tk
from datetime import date, datetime
from tkinter import scrolledtext
from dotenv import load_dotenv
from google import genai

# ================= ENV =================
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# ================= CONFIG =================
LOG_DIR = "logs"
MODEL_NAME = "gemini-3-flash-preview"

BG_MAIN = "#2E3440"
BG_INPUT = "#3B4252"
FG_TEXT = "#D8DEE9"
ACCENT = "#88C0D0"
SUCCESS = "#A3BE8C"
ERROR = "#BF616A"
HIGHLIGHT = "#EBCB8B"

QUOTES = [
    "You are building discipline, not chasing motivation.",
    "Progress compounds quietly. Keep going.",
    "Even showing up tired is a form of strength.",
    "Consistency beats intensity every single time.",
    "You don’t need confidence — you need momentum.",
    "This effort will matter more than you realize.",
    "Focus on today’s brick. The wall builds itself.",
    "Rest if needed. Don’t quit.",
    "Your future self is watching. Make them proud.",
    "Hard days are data, not failure."
]

# ================= UI HELPERS =================
def popup(title, msg, color=ACCENT):
    win = tk.Toplevel(root)
    win.title(title)
    win.geometry("360x180")
    win.configure(bg=BG_INPUT)
    win.transient(root)
    win.grab_set()

    tk.Label(win, text=title.upper(), fg=color, bg=BG_INPUT,
             font=("Segoe UI", 10, "bold")).pack(pady=(20, 10))
    tk.Label(win, text=msg, fg=FG_TEXT, bg=BG_INPUT,
             wraplength=320, font=("Segoe UI", 10)).pack(pady=10)

    tk.Button(win, text="OK", command=win.destroy,
              bg=BG_MAIN, fg=FG_TEXT,
              font=("Segoe UI", 9, "bold"),
              relief="flat", padx=20, pady=6).pack(pady=15)

# ================= FILE LOGIC =================
def ensure_log_dir():
    os.makedirs(LOG_DIR, exist_ok=True)

def today_file():
    today = date.today().isoformat()
    return os.path.join(LOG_DIR, f"{today}.md"), today

def save_log():
    did = did_text.get("1.0", tk.END).strip()
    blockers = challenges_text.get("1.0", tk.END).strip()
    learn = learned_text.get("1.0", tk.END).strip()

    if not (did or blockers or learn) or did.startswith("//"):
        popup("Nothing Saved", "Write something meaningful first ✨", HIGHLIGHT)
        return

    ensure_log_dir()
    path, today = today_file()
    now = datetime.now().strftime("%I:%M %p")

    is_new = not os.path.exists(path)

    with open(path, "a", encoding="utf-8") as f:
        if is_new:
            f.write(f"# 📅 Log for {today}\n\n")
        f.write(f"---\n### 🕒 {now}\n")
        if did: f.write(f"**Progress:**\n{did}\n\n")
        if blockers: f.write(f"**Blockers:**\n{blockers}\n\n")
        if learn: f.write(f"**Learnings:**\n{learn}\n\n")

    popup("Saved", "Entry logged successfully ✅", SUCCESS)
    for box in (did_text, challenges_text, learned_text):
        box.delete("1.0", tk.END)

# ================= AI =================
def summarize():
    path, _ = today_file()
    if not os.path.exists(path):
        popup("Missing Log", "Save a log first.", HIGHLIGHT)
        return

    def run():
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            prompt = (
                "Summarize this log professionally.\n"
                "- Bullet points\n"
                "- 2 sentences for Learnings\n"
                "- 2 sentences for Blockers\n\n"
                f"{content}"
            )

            res = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt
            )

            summary_box.delete("1.0", tk.END)
            summary_box.insert(tk.END, res.text.strip())
        except Exception as e:
            popup("AI Error", str(e), ERROR)

    threading.Thread(target=run).start()

# ================= GIT =================
def git_commit_push():
    def run():
        try:
            status = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True, text=True
            )

            if not status.stdout.strip():
                popup("Git", "No new changes to commit 🙂", HIGHLIGHT)
                return

            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(
                ["git", "commit", "-m", f"Daily log update: {date.today()}"],
                check=True, capture_output=True, text=True
            )
            subprocess.run(["git", "push"], check=True, capture_output=True, text=True)

            popup("Git Success", "Synced with GitHub 🚀", SUCCESS)

        except subprocess.CalledProcessError as e:
            msg = e.stderr.strip() if e.stderr else str(e)
            popup("Git Error", msg, ERROR)

    threading.Thread(target=run).start()

# ================= UI =================
root = tk.Tk()
root.title("DeepWork Logger")
root.geometry("800x850")
root.configure(bg=BG_MAIN)

frame = tk.Frame(root, bg=BG_MAIN)
frame.pack(fill="both", expand=True)

def section(label, h):
    tk.Label(frame, text=label, fg=HIGHLIGHT, bg=BG_MAIN,
             font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=40, pady=(20, 5))
    t = tk.Text(frame, height=h, bg=BG_INPUT, fg=FG_TEXT,
                font=("Consolas", 11), relief="flat",
                padx=12, pady=8, insertbackground=FG_TEXT)
    t.pack(fill="x", padx=40)

    quote = random.choice(QUOTES)
    t.insert("1.0", f"// {quote}")
    t.bind("<FocusIn>", lambda e: t.delete("1.0", tk.END)
           if t.get("1.0", tk.END).startswith("//") else None)
    return t

did_text = section("COMPLETED TASKS", 5)
challenges_text = section("BLOCKERS", 4)
learned_text = section("LEARNINGS", 4)

btns = tk.Frame(frame, bg=BG_MAIN)
btns.pack(fill="x", padx=40, pady=25)

tk.Button(btns, text="💾 SAVE ENTRY", command=save_log,
          bg=ACCENT, fg=BG_MAIN, relief="flat",
          font=("Segoe UI", 9, "bold"),
          padx=20, pady=12).pack(side="left", expand=True, fill="x", padx=5)

tk.Button(btns, text="🤖 AI SUMMARY", command=summarize,
          bg=SUCCESS, fg=BG_MAIN, relief="flat",
          font=("Segoe UI", 9, "bold"),
          padx=20, pady=12).pack(side="left", expand=True, fill="x", padx=5)

tk.Label(frame, text="VERSION CONTROL", fg=HIGHLIGHT, bg=BG_MAIN,
         font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=40, pady=(15, 5))

tk.Button(frame, text="🚀 COMMIT & PUSH TO GITHUB",
          command=git_commit_push,
          bg=BG_MAIN, fg=SUCCESS,
          highlightbackground=SUCCESS,
          highlightthickness=1,
          relief="flat",
          font=("Segoe UI", 9, "bold"),
          padx=20, pady=14).pack(fill="x", padx=40, pady=(0, 40))

root.mainloop()