import os
import sys
import zipfile
import shutil
import tkinter as tk
from tkinter import ttk
# Import TkinterDnD - Installation check is important
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
except ImportError:
    print("Error: tkinterdnd2 library not found.")
    print("Please install it by running: pip install tkinterdnd2")
    sys.exit(1)

# --- Constants ---
SUBTITLE_EXTENSIONS = {'.srt', '.sub', '.ass', '.vtt', '.ssa'}
VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv'} # For identifying movie files

# Define some basic colors and styles
STYLE_CONFIG = {
    "bg_color": "#f0f0f0",
    "drop_bg_idle": "#ffffff",
    "drop_bg_hover": "#e0e0ff",
    "drop_border_color": "#a0a0a0",
    "text_color": "#333333",
    "success_color": "#008000",
    "error_color": "#ff0000",
    "font_normal": ("Segoe UI", 10),
    "font_bold": ("Segoe UI", 10, "bold"),
    "font_large": ("Segoe UI", 12, "bold"),
}

# --- Processing Logic (Adapted from previous script) ---
def process_subtitle_zip(movie_path, zip_path, status_callback):
    """
    Extracts, moves, and renames subtitle. Updates GUI via status_callback.

    Args:
        movie_path (str): Full path to the movie file.
        zip_path (str): Full path to the zip archive.
        status_callback (callable): Function to call with status updates.

    Returns:
        bool: True if successful, False otherwise.
    """
    def update_status(message, is_error=False):
        """Helper to call the callback"""
        print(message) # Also print to console for debugging
        status_callback(message, is_error)

    update_status(f"Processing started...")
    # --- 1. Validate Input Paths ---
    if not movie_path or not os.path.isfile(movie_path):
        update_status(f"Error: Movie file path is missing or invalid: '{movie_path}'", True)
        return False
    if not zip_path or not os.path.isfile(zip_path):
        update_status(f"Error: Zip file path is missing or invalid: '{zip_path}'", True)
        return False

    update_status(f"Movie: {os.path.basename(movie_path)}")
    update_status(f"Zip: {os.path.basename(zip_path)}")

    # --- 2. Determine Paths and Names ---
    movie_dir = os.path.dirname(movie_path)
    movie_basename_no_ext = os.path.splitext(os.path.basename(movie_path))[0]
    temp_extract_dir = os.path.join(movie_dir, f"_temp_extract_{os.path.basename(zip_path)}")

    try:
        # --- 3. Extract the Zip File ---
        update_status(f"Extracting '{os.path.basename(zip_path)}'...")
        os.makedirs(temp_extract_dir, exist_ok=True)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_extract_dir)
        update_status(f"Extracted to temporary directory.")

        # --- 4. Find the Subtitle File ---
        found_subtitle_original_path = None
        found_subtitle_ext = None
        update_status("Searching for subtitle file...")
        for root, dirs, files in os.walk(temp_extract_dir):
            for file in files:
                file_ext_lower = os.path.splitext(file)[1].lower()
                if file_ext_lower in SUBTITLE_EXTENSIONS:
                    current_subtitle_path = os.path.join(root, file)
                    if found_subtitle_original_path:
                        update_status(f"Warning: Multiple subs found. Using first: '{os.path.basename(found_subtitle_original_path)}'")
                        break
                    else:
                        found_subtitle_original_path = current_subtitle_path
                        found_subtitle_ext = os.path.splitext(file)[1] # Keep original case
                        update_status(f"Found subtitle: '{file}'")
            if found_subtitle_original_path:
                break

        if not found_subtitle_original_path:
            update_status(f"Error: No subtitle file ({', '.join(SUBTITLE_EXTENSIONS)}) found in zip.", True)
            return False

        # --- 5. Determine Target Path and Rename/Move ---
        target_subtitle_name = f"{movie_basename_no_ext}{found_subtitle_ext}"
        target_subtitle_path = os.path.join(movie_dir, target_subtitle_name)
        update_status(f"Moving subtitle to: '{target_subtitle_name}'")

        if os.path.exists(target_subtitle_path):
            update_status(f"Warning: Overwriting existing file: '{target_subtitle_name}'")

        shutil.move(found_subtitle_original_path, target_subtitle_path)
        update_status("Subtitle processed successfully!", is_error=False) # Explicitly mark success
        return True

    except zipfile.BadZipFile:
        update_status(f"Error: '{os.path.basename(zip_path)}' is not a valid zip file.", True)
        return False
    except PermissionError as e:
         update_status(f"Error: Permission denied. Check permissions. Details: {e}", True)
         return False
    except Exception as e:
        update_status(f"An unexpected error occurred: {e}", True)
        return False
    finally:
        # --- 6. Clean Up Temporary Directory ---
        if os.path.exists(temp_extract_dir):
            update_status(f"Cleaning up temporary files...")
            try:
                shutil.rmtree(temp_extract_dir)
            except OSError as e:
                update_status(f"Warning: Could not remove temp directory '{temp_extract_dir}'. Error: {e}")


# --- GUI Application Class ---
class SubtitleApp(TkinterDnD.Tk): # Inherit from TkinterDnD.Tk
    def __init__(self):
        super().__init__() # Initialize the TkinterDnD Tk window

        self.title("Subtitle Helper")
        self.geometry("500x350") # Adjusted size
        self.configure(bg=STYLE_CONFIG["bg_color"])

        # Variables to store dropped file paths
        self.movie_file_path = tk.StringVar()
        self.zip_file_path = tk.StringVar()

        # --- Create Widgets ---
        title_label = ttk.Label(
            self, text="Drag & Drop Files or Drag Files onto Script",
            font=STYLE_CONFIG["font_large"], background=STYLE_CONFIG["bg_color"],
            foreground=STYLE_CONFIG["text_color"]
        )
        title_label.pack(pady=(15, 10))

        drop_frame = ttk.Frame(self, style="App.TFrame")
        drop_frame.pack(pady=10, padx=20, fill=tk.X, expand=False)
        drop_frame.columnconfigure(0, weight=1)
        drop_frame.columnconfigure(1, weight=1)

        style = ttk.Style(self)
        style.configure("App.TFrame", background=STYLE_CONFIG["bg_color"])
        style.configure("Drop.TLabel",
                        background=STYLE_CONFIG["drop_bg_idle"],
                        foreground=STYLE_CONFIG["text_color"],
                        borderwidth=2, relief=tk.SOLID, padding=10,
                        anchor=tk.CENTER, font=STYLE_CONFIG["font_normal"])
        style.map("Drop.TLabel", relief=[('active', tk.RAISED)],
                  background=[('active', STYLE_CONFIG["drop_bg_hover"])])

        self.movie_drop_label = ttk.Label(
            drop_frame, text="Drop Movie File Here\n(e.g., .mp4, .mkv, .avi)",
            style="Drop.TLabel", width=30
        )
        self.movie_drop_label.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.movie_drop_label.drop_target_register(DND_FILES)
        self.movie_drop_label.dnd_bind('<<Drop>>', self.handle_drop)
        self.movie_drop_label.dnd_bind('<<DragEnter>>', lambda e: self.update_drop_style(e.widget, hover=True))
        self.movie_drop_label.dnd_bind('<<DragLeave>>', lambda e: self.update_drop_style(e.widget, hover=False))

        self.zip_drop_label = ttk.Label(
            drop_frame, text="Drop Subtitle Zip File Here\n(.zip)",
            style="Drop.TLabel", width=30
        )
        self.zip_drop_label.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.zip_drop_label.drop_target_register(DND_FILES)
        self.zip_drop_label.dnd_bind('<<Drop>>', self.handle_drop)
        self.zip_drop_label.dnd_bind('<<DragEnter>>', lambda e: self.update_drop_style(e.widget, hover=True))
        self.zip_drop_label.dnd_bind('<<DragLeave>>', lambda e: self.update_drop_style(e.widget, hover=False))

        self.status_label = ttk.Label(
            self, text="Waiting for files...", font=STYLE_CONFIG["font_normal"],
            background=STYLE_CONFIG["bg_color"], foreground=STYLE_CONFIG["text_color"],
            wraplength=450
        )
        self.status_label.pack(pady=(15, 10), padx=20, fill=tk.X)

        reset_button = ttk.Button(self, text="Reset", command=self.reset_ui)
        reset_button.pack(pady=(0, 15))

    def update_drop_style(self, widget, hover=False):
        if hover:
            widget.configure(background=STYLE_CONFIG["drop_bg_hover"])
        else:
            widget.configure(background=STYLE_CONFIG["drop_bg_idle"])

    def set_file(self, file_path, file_type):
        """
        Sets a file (movie or zip), updates UI, and returns success.
        Args:
            file_path (str): The path to the file.
            file_type (str): "movie" or "zip".
        Returns:
            bool: True if file was successfully set, False otherwise.
        """
        if not os.path.isfile(file_path):
            self.update_status_display(f"Error: {file_type.capitalize()} path invalid: '{os.path.basename(file_path)}'", True)
            return False

        file_name = os.path.basename(file_path)
        file_ext = os.path.splitext(file_name)[1].lower()

        if file_type == "movie":
            if file_ext in VIDEO_EXTENSIONS:
                self.movie_file_path.set(file_path)
                self.movie_drop_label.configure(text=f"Movie:\n{file_name}", font=STYLE_CONFIG["font_bold"])
                self.update_status_display(f"Movie file set: {file_name}")
                return True
            else:
                self.update_status_display(f"Error: '{file_name}' is not a recognized movie file.", True)
                return False
        elif file_type == "zip":
            if file_ext == '.zip':
                self.zip_file_path.set(file_path)
                self.zip_drop_label.configure(text=f"Zip:\n{file_name}", font=STYLE_CONFIG["font_bold"])
                self.update_status_display(f"Zip file set: {file_name}")
                return True
            else:
                self.update_status_display(f"Error: '{file_name}' is not a .zip file.", True)
                return False
        return False


    def handle_drop(self, event):
        files = self.tk.splitlist(event.data)
        if not files:
            self.update_status_display("No files detected in drop.", True)
            return

        dropped_file_path = files[0]
        target_widget = event.widget
        self.update_drop_style(target_widget, hover=False)

        file_successfully_set = False
        if target_widget == self.movie_drop_label:
            file_successfully_set = self.set_file(dropped_file_path, "movie")
        elif target_widget == self.zip_drop_label:
            file_successfully_set = self.set_file(dropped_file_path, "zip")

        if file_successfully_set:
            self.check_and_run_processing()

    def check_and_run_processing(self):
        movie_path = self.movie_file_path.get()
        zip_path = self.zip_file_path.get()

        if movie_path and zip_path:
            self.update_status_display("Both files ready. Starting process...")
            process_subtitle_zip(movie_path, zip_path, self.update_status_display)

    def update_status_display(self, message, is_error=False):
        if is_error:
            self.status_label.configure(text=message, foreground=STYLE_CONFIG["error_color"])
        elif "success" in message.lower() or "successfully" in message.lower() : # Success is a keyword
             self.status_label.configure(text=message, foreground=STYLE_CONFIG["success_color"])
        else: # Neutral or informational message
            self.status_label.configure(text=message, foreground=STYLE_CONFIG["text_color"])
        self.update_idletasks()

    def reset_ui(self, clear_status=True):
        self.movie_file_path.set("")
        self.zip_file_path.set("")
        self.movie_drop_label.configure(
            text="Drop Movie File Here\n(e.g., .mp4, .mkv, .avi)",
            font=STYLE_CONFIG["font_normal"],
            background=STYLE_CONFIG["drop_bg_idle"]
        )
        self.zip_drop_label.configure(
            text="Drop Subtitle Zip File Here\n(.zip)",
            font=STYLE_CONFIG["font_normal"],
            background=STYLE_CONFIG["drop_bg_idle"]
        )
        if clear_status:
            self.update_status_display("Waiting for files...")
        print("UI Reset.")


# --- Main execution ---
if __name__ == "__main__":
    app = SubtitleApp()

    args = sys.argv[1:]
    files_successfully_set_from_args = 0
    
    if args:
        print(f"Arguments received: {sys.argv[1:]}")
        
        movie_arg_found_and_set = False
        zip_arg_found_and_set = False
        
        # Try to set the first valid movie and first valid zip from args
        for arg_path in args:
            if not os.path.isfile(arg_path):
                print(f"Info: Argument '{os.path.basename(arg_path)}' is not a file, skipping.")
                # Optionally update GUI status if it's a critical error for an arg
                # app.update_status_display(f"Arg Error: '{os.path.basename(arg_path)}' not found.", True)
                continue

            file_ext = os.path.splitext(arg_path)[1].lower()

            if not movie_arg_found_and_set and file_ext in VIDEO_EXTENSIONS:
                if app.set_file(arg_path, "movie"):
                    movie_arg_found_and_set = True
                    files_successfully_set_from_args += 1
            elif not zip_arg_found_and_set and file_ext == '.zip':
                if app.set_file(arg_path, "zip"):
                    zip_arg_found_and_set = True
                    files_successfully_set_from_args += 1
        
        # Update status based on what was loaded from arguments
        if movie_arg_found_and_set and zip_arg_found_and_set:
            # `set_file` would have updated status for each, `check_and_run_processing` will state "Both files ready..."
            pass 
        elif movie_arg_found_and_set:
            app.update_status_display(f"Movie '{os.path.basename(app.movie_file_path.get())}' loaded from args. Drop ZIP.", False)
        elif zip_arg_found_and_set:
            app.update_status_display(f"ZIP '{os.path.basename(app.zip_file_path.get())}' loaded from args. Drop Movie.", False)
        elif args and files_successfully_set_from_args == 0: 
            # Args were provided, but no movie or zip was successfully set from them.
            # `set_file` would show specific errors for wrong types or invalid paths.
            # This is a fallback status if nothing got loaded.
            arg_basenames = [os.path.basename(p) for p in args]
            app.update_status_display(f"Args: No movie/ZIP identified or set from: {', '.join(arg_basenames)}. Waiting for files.", True)

        # If any files were successfully set from arguments, check if processing can start
        if files_successfully_set_from_args > 0:
            app.check_and_run_processing()

    app.mainloop()