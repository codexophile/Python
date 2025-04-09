import os
import sys
import zipfile
import shutil
import tkinter as tk
from tkinter import ttk
from tkinterdnd2 import DND_FILES, TkinterDnD # Import TkinterDnD

# --- Installation Check ---
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
except ImportError:
    print("Error: tkinterdnd2 library not found.")
    print("Please install it by running: pip install tkinterdnd2")
    sys.exit(1)

# --- Constants ---
SUBTITLE_EXTENSIONS = {'.srt', '.sub', '.ass', '.vtt', '.ssa'}
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
        # Title Label
        title_label = ttk.Label(
            self,
            text="Drag & Drop Files",
            font=STYLE_CONFIG["font_large"],
            background=STYLE_CONFIG["bg_color"],
            foreground=STYLE_CONFIG["text_color"]
        )
        title_label.pack(pady=(15, 10))

        # Frame for Drop Zones
        drop_frame = ttk.Frame(self, style="App.TFrame")
        drop_frame.pack(pady=10, padx=20, fill=tk.X, expand=False)
        drop_frame.columnconfigure(0, weight=1)
        drop_frame.columnconfigure(1, weight=1)

        # Style for frames
        style = ttk.Style(self)
        style.configure("App.TFrame", background=STYLE_CONFIG["bg_color"])
        style.configure("Drop.TLabel",
                        background=STYLE_CONFIG["drop_bg_idle"],
                        foreground=STYLE_CONFIG["text_color"],
                        borderwidth=2,
                        relief=tk.SOLID,
                        padding=10,
                        anchor=tk.CENTER,
                        font=STYLE_CONFIG["font_normal"])
        style.map("Drop.TLabel",
                  relief=[('active', tk.RAISED)],
                  background=[('active', STYLE_CONFIG["drop_bg_hover"])])


        # Movie Drop Zone
        self.movie_drop_label = ttk.Label(
            drop_frame,
            text="Drop Movie File Here\n(e.g., .mp4, .mkv, .avi)",
            style="Drop.TLabel",
            width=30 # Approx width
        )
        self.movie_drop_label.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        # Make the label a drop target that accepts files
        self.movie_drop_label.drop_target_register(DND_FILES)
        self.movie_drop_label.dnd_bind('<<Drop>>', self.handle_drop)
        self.movie_drop_label.dnd_bind('<<DragEnter>>', lambda e: self.update_drop_style(e.widget, hover=True))
        self.movie_drop_label.dnd_bind('<<DragLeave>>', lambda e: self.update_drop_style(e.widget, hover=False))


        # Zip Drop Zone
        self.zip_drop_label = ttk.Label(
            drop_frame,
            text="Drop Subtitle Zip File Here\n(.zip)",
            style="Drop.TLabel",
            width=30 # Approx width
        )
        self.zip_drop_label.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        # Make the label a drop target
        self.zip_drop_label.drop_target_register(DND_FILES)
        self.zip_drop_label.dnd_bind('<<Drop>>', self.handle_drop)
        self.zip_drop_label.dnd_bind('<<DragEnter>>', lambda e: self.update_drop_style(e.widget, hover=True))
        self.zip_drop_label.dnd_bind('<<DragLeave>>', lambda e: self.update_drop_style(e.widget, hover=False))

        # Status Label
        self.status_label = ttk.Label(
            self,
            text="Waiting for files...",
            font=STYLE_CONFIG["font_normal"],
            background=STYLE_CONFIG["bg_color"],
            foreground=STYLE_CONFIG["text_color"],
            wraplength=450 # Wrap text if long
        )
        self.status_label.pack(pady=(15, 10), padx=20, fill=tk.X)

        # Reset Button
        reset_button = ttk.Button(self, text="Reset", command=self.reset_ui)
        reset_button.pack(pady=(0, 15))

    def update_drop_style(self, widget, hover=False):
        """Changes drop target appearance on drag hover."""
        if hover:
            widget.configure(background=STYLE_CONFIG["drop_bg_hover"])
        else:
            widget.configure(background=STYLE_CONFIG["drop_bg_idle"])

    def handle_drop(self, event):
        """Handles the drop event for both zones."""
        # event.data contains a string with space-separated, brace-enclosed paths
        # We need to parse this carefully.
        # Example: '{/path/to/file1 with space} {/path/to/file2}'
        files = self.tk.splitlist(event.data) # Use tk.splitlist for correct parsing

        if not files:
            self.update_status("No files detected in drop.", True)
            return

        # Assume only one file is dropped per zone for simplicity
        dropped_file_path = files[0]
        file_name = os.path.basename(dropped_file_path)
        file_ext = os.path.splitext(file_name)[1].lower()

        # Determine which drop zone received the file
        target_widget = event.widget

        # Reset hover style
        self.update_drop_style(target_widget, hover=False)

        is_movie_zone = (target_widget == self.movie_drop_label)
        is_zip_zone = (target_widget == self.zip_drop_label)

        if is_movie_zone:
            # Basic check for common video extensions (can be expanded)
            if file_ext in ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv']:
                self.movie_file_path.set(dropped_file_path)
                self.movie_drop_label.configure(text=f"Movie:\n{file_name}", font=STYLE_CONFIG["font_bold"])
                self.update_status(f"Movie file selected: {file_name}")
            else:
                self.update_status(f"Error: Dropped file '{file_name}' doesn't look like a movie file.", True)
                return # Don't proceed if wrong file type

        elif is_zip_zone:
            if file_ext == '.zip':
                self.zip_file_path.set(dropped_file_path)
                self.zip_drop_label.configure(text=f"Zip:\n{file_name}", font=STYLE_CONFIG["font_bold"])
                self.update_status(f"Zip file selected: {file_name}")
            else:
                self.update_status(f"Error: Dropped file '{file_name}' is not a .zip file.", True)
                return # Don't proceed if wrong file type

        # Check if both files are now set and trigger processing
        self.check_and_run_processing()

    def check_and_run_processing(self):
        """Checks if both files are provided and runs the main logic."""
        movie_path = self.movie_file_path.get()
        zip_path = self.zip_file_path.get()

        if movie_path and zip_path:
            # Disable drop zones during processing? (Optional)
            # self.movie_drop_label.drop_target_unregister()
            # self.zip_drop_label.drop_target_unregister()

            self.update_status("Both files ready. Starting process...")
            # Run the processing function, passing the GUI update method
            success = process_subtitle_zip(movie_path, zip_path, self.update_status_display)

            # Re-enable drop zones if they were disabled
            # self.movie_drop_label.drop_target_register(DND_FILES)
            # self.zip_drop_label.drop_target_register(DND_FILES)

            # Optionally reset after success/failure, or leave as is
            # if success:
            #    self.reset_ui(clear_status=False) # Keep success message
            # else:
            #    # Keep error message and file names displayed
            #    pass

    def update_status_display(self, message, is_error=False):
        """Updates the status label in the GUI."""
        if is_error:
            self.status_label.configure(text=message, foreground=STYLE_CONFIG["error_color"])
        elif "success" in message.lower():
             self.status_label.configure(text=message, foreground=STYLE_CONFIG["success_color"])
        else:
            self.status_label.configure(text=message, foreground=STYLE_CONFIG["text_color"])
        self.update_idletasks() # Force GUI update

    def reset_ui(self, clear_status=True):
        """Resets the UI to its initial state."""
        self.movie_file_path.set("")
        self.zip_file_path.set("")
        self.movie_drop_label.configure(
            text="Drop Movie File Here\n(e.g., .mp4, .mkv, .avi)",
            font=STYLE_CONFIG["font_normal"]
        )
        self.zip_drop_label.configure(
            text="Drop Subtitle Zip File Here\n(.zip)",
            font=STYLE_CONFIG["font_normal"]
        )
        if clear_status:
            self.update_status_display("Waiting for files...")
        print("UI Reset.")


# --- Main execution ---
if __name__ == "__main__":
    app = SubtitleApp()
    app.mainloop()
