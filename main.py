import os
import subprocess
from datetime import date
import tkinter as tk
from tkinter import messagebox, scrolledtext

from google import genai


# ---------------- CONFIG ----------------
LOG_DIR = "logs"
MODEL_NAME = "gemini-1.5-flash"
# ----------------------------------------


def ensure_log_dir():
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)


def get_today_file():
    today = date.today().isoformat()
    return os.path.join(LOG_DIR, f"{today}.md"), today


def save_log():
    did = did_text.get("1.0", tk.END).strip()
    challenges = challenges_text.get("1.0", tk.END).strip()
    learned = learned_text.get("1.0", tk.END).strip()

    if not (did or challenges or learned):
        messagebox.showwarning("Empty", "Write something first 🙂")
        return

    ensure_log_dir()
    file_path, today = get_today_file()
    new_file = not os.path.exists(file_path)

    with open(file_path, "a", encoding="utf-8") as f:
        if new_file:
            f.write(f"# {today}\n\n")

        if did:
            f.write("## What I did\n")
            for line in did.split("\n"):
                f.write(f"- {line}\n")
            f.write("\n")

        if challenges:
            f.write("## Challenges\n")
            for line in challenges.split("\n"):
                f.write(f"- {line}\n")
            f.write("\n")

        if learned:
            f.write("## What I learned\n")
            for line in learned.split("\n"):
                f.write(f"- {line}\n")
            f.write("\n")

    messagebox.showinfo("Saved", "Daily log saved ✅")


def generate_summary():
    file_path, _ = get_today_file()
    if not os.path.exists(file_path):
        messagebox.showerror("No log", "Save today’s log first.")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    try:
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    except KeyError:
        messagebox.showerror("API Key Missing", "Set GEMINI_API_KEY environment variable.")
        return

    model = genai.GenerativeModel(MODEL_NAME)

    prompt = f"""
Summarize the following daily work log into concise, professional bullet points
suitable for sending as a daily update to a manager:

{content}
"""

    try:
        response = model.generate_content(prompt)
        summary_box.delete("1.0", tk.END)
        summary_box.insert(tk.END, response.text.strip())
    except Exception as e:
        messagebox.showerror("Error", str(e))


def git_commit():
    file_path, today = get_today_file()
    if not os.path.exists(file_path):
        messagebox.showerror("No log", "Nothing to commit yet.")
        return

    try:
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", f"Daily log: {today}"], check=True)
        subprocess.run(["git", "push"], check=True)
        messagebox.showinfo("Git", "Committed & pushed to GitHub 🚀")
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Git Error", str(e))


# ---------------- GUI ----------------
root = tk.Tk()
root.title("Daily Work Logger")
root.geometry("700x750")

tk.Label(root, text="What I did today").pack(anchor="w", padx=10)
did_text = scrolledtext.ScrolledText(root, height=5)
did_text.pack(fill="x", padx=10, pady=5)

tk.Label(root, text="Challenges faced").pack(anchor="w", padx=10)
challenges_text = scrolledtext.ScrolledText(root, height=5)
challenges_text.pack(fill="x", padx=10, pady=5)

tk.Label(root, text="What I learned").pack(anchor="w", padx=10)
learned_text = scrolledtext.ScrolledText(root, height=5)
learned_text.pack(fill="x", padx=10, pady=5)

tk.Button(root, text="Save Log", command=save_log).pack(pady=10)

tk.Label(root, text="AI Summary (copy & send)").pack(anchor="w", padx=10)
summary_box = scrolledtext.ScrolledText(root, height=8)
summary_box.pack(fill="x", padx=10, pady=5)

tk.Button(root, text="Generate Summary (Gemini)", command=generate_summary).pack(pady=5)
tk.Button(root, text="Commit to GitHub", command=git_commit).pack(pady=5)

root.mainloop()