import os
import tkinter as tk
from tkinter import filedialog, messagebox
from moviepy.editor import VideoFileClip
from pytoon.animator import animate  # <-- Import your 'animate' class from animator.py

def browse_file(entry_widget, filetypes=None):
    """Opens a file dialog and updates the entry widget with the selected path."""
    if filetypes is None:
        filetypes = [("All files", "*.*")]

    path = filedialog.askopenfilename(filetypes=filetypes)
    if path:
        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, path)

def browse_folder(entry_widget):
    """Opens a folder dialog and updates the entry widget with the selected folder path."""
    folder = filedialog.askdirectory()
    if folder:
        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, folder)

def run_animation():
    """Collect parameters from the UI and run the animation/export process."""
    audio_path = entry_audio.get().strip()
    bg_path = entry_bg.get().strip()
    viseme_set = entry_viseme.get().strip()
    x_pos = entry_x.get().strip()
    y_pos = entry_y.get().strip()
    sx = entry_sx.get().strip()
    sy = entry_sy.get().strip()

    # Basic validation
    if not os.path.isfile(audio_path):
        messagebox.showerror("Error", "Audio file path is invalid.")
        return
    if not os.path.exists(bg_path):
        messagebox.showerror("Error", "Background path is invalid.")
        return

    # Convert numeric fields
    try:
        x_pos = int(x_pos)
        y_pos = int(y_pos)
        sx = float(sx)
        sy = float(sy)
    except ValueError:
        messagebox.showerror("Error", "Position/Scale fields must be numeric.")
        return

    # Create the animator instance
    # If your 'animate' class expects a 'transcript' or uses the viseme_set in some way,
    # adapt accordingly. For now, let's assume we just pass the audio, maybe the set is used internally.
    anim = animate(audio_file=audio_path, transcript=None, fps=30)  # or the FPS you want

    # If your code uses the viseme_set path, you might do something like:
    # anim.set_viseme_directory(viseme_set)  # hypothetical method
    # Or if the 'viseme_sequencer' itself needs a custom path, you'd handle that in your code.

    # Prompt for output file
    output_path = filedialog.asksaveasfilename(
        defaultextension=".mp4",
        filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")]
    )
    if not output_path:
        return  # user canceled

    try:
        # Determine if background is a video or image
        if bg_path.lower().endswith(('.png', '.jpg', '.jpeg')):
            bg_source = bg_path  # let the animator handle it as ImageClip
        else:
            bg_source = VideoFileClip(bg_path)

        # Export the final animation
        anim.export(
            path=output_path,
            background=bg_source,
            mouth_x=x_pos,
            mouth_y=y_pos,
            scale_x=sx,
            scale_y=sy
        )
        messagebox.showinfo("Success", f"Animation exported to: {output_path}")

    except Exception as e:
        messagebox.showerror("Error", str(e))

# ---------------- MAIN GUI SETUP ----------------

root = tk.Tk()
root.title("Mouth Animation GUI")

# Row 1: Audio
lbl_audio = tk.Label(root, text="Audio File:")
lbl_audio.grid(row=0, column=0, padx=5, pady=5, sticky="e")
entry_audio = tk.Entry(root, width=60)
entry_audio.grid(row=0, column=1, padx=5, pady=5)
btn_audio = tk.Button(root, text="Browse", command=lambda: browse_file(entry_audio, [("Audio Files", "*.wav *.mp3 *.ogg *.flac"), ("All Files", "*.*")]))
btn_audio.grid(row=0, column=2, padx=5, pady=5)

# Row 2: Background (can be image or video)
lbl_bg = tk.Label(root, text="Background File:")
lbl_bg.grid(row=1, column=0, padx=5, pady=5, sticky="e")
entry_bg = tk.Entry(root, width=60)
entry_bg.grid(row=1, column=1, padx=5, pady=5)
btn_bg = tk.Button(root, text="Browse", command=lambda: browse_file(entry_bg))
btn_bg.grid(row=1, column=2, padx=5, pady=5)

# Row 3: Viseme set (folder)
lbl_viseme = tk.Label(root, text="Viseme Set Folder:")
lbl_viseme.grid(row=2, column=0, padx=5, pady=5, sticky="e")
entry_viseme = tk.Entry(root, width=60)
entry_viseme.grid(row=2, column=1, padx=5, pady=5)
btn_viseme = tk.Button(root, text="Browse", command=lambda: browse_folder(entry_viseme))
btn_viseme.grid(row=2, column=2, padx=5, pady=5)

# Row 4: X position
lbl_x = tk.Label(root, text="Mouth X (center):")
lbl_x.grid(row=3, column=0, padx=5, pady=5, sticky="e")
entry_x = tk.Entry(root, width=10)
entry_x.insert(0, "200")  # default example
entry_x.grid(row=3, column=1, padx=5, pady=5, sticky="w")

# Row 5: Y position
lbl_y = tk.Label(root, text="Mouth Y (center):")
lbl_y.grid(row=4, column=0, padx=5, pady=5, sticky="e")
entry_y = tk.Entry(root, width=10)
entry_y.insert(0, "300")  # default example
entry_y.grid(row=4, column=1, padx=5, pady=5, sticky="w")

# Row 6: Scale X
lbl_sx = tk.Label(root, text="Scale X:")
lbl_sx.grid(row=5, column=0, padx=5, pady=5, sticky="e")
entry_sx = tk.Entry(root, width=10)
entry_sx.insert(0, "1.0")  # default
entry_sx.grid(row=5, column=1, padx=5, pady=5, sticky="w")

# Row 7: Scale Y
lbl_sy = tk.Label(root, text="Scale Y:")
lbl_sy.grid(row=6, column=0, padx=5, pady=5, sticky="e")
entry_sy = tk.Entry(root, width=10)
entry_sy.insert(0, "1.0")  # default
entry_sy.grid(row=6, column=1, padx=5, pady=5, sticky="w")

# Row 8: Run button
btn_run = tk.Button(root, text="Generate Animation", command=run_animation)
btn_run.grid(row=7, column=0, columnspan=3, pady=10)

root.mainloop()
