import os
import re
import tkinter as tk
from tkinter import ttk, messagebox
import winreg
from PIL import Image, ImageTk


class WallpaperManager:
    """Main application class for managing Windows wallpaper history"""
    
    def __init__(self, root):
        """Initialize the application with UI components and event bindings"""
        self.root = root
        self.thumbnail_refs = {}
        self.resize_job = None
        self.setup_window()
        self.setup_colors()
        self.configure_styles()
        self.create_layout()
        self.initialize_components()
        self.image_cache = self.get_image_cache()
        self.populate_image_list()
        
    def setup_window(self):
        """Configure the main application window"""
        self.root.title("Wallpaper Manager")
        self.root.geometry("1100x680")
        self.root.minsize(780, 520)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.root.configure(bg="#12161d")
        
        # Set window icon
        try:
            self.root.iconbitmap("wallpaper.ico")
        except:
            pass  # Ignore if icon file isn't available
    
    def setup_colors(self):
        """Define color scheme for the application"""
        # Dark color palette
        self.colors = {
            "primary": "#4f8cff",
            "primary_dark": "#2f6fed",
            "secondary": "#22c55e",
            "danger": "#ef4444",
            "neutral": "#334155",
            "bg_light": "#151a22",
            "bg_dark": "#0f131a",
            "text_light": "#e5e7eb",
            "text_dark": "#cbd5e1",
            "border": "#2a3442",
        }
        
    def configure_styles(self):
        """Set up custom styles for UI components"""
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        # Configure basic styles
        self.style.configure("TFrame", background=self.colors["bg_light"])
        self.style.configure("TLabel", background=self.colors["bg_light"], foreground=self.colors["text_dark"])
        self.style.configure("TButton", background=self.colors["neutral"], foreground=self.colors["text_light"], padding=5)
        self.style.configure("Card.TFrame", background=self.colors["bg_dark"], relief="solid", borderwidth=1)
        self.style.configure("Card.TLabel", background=self.colors["bg_dark"])
        self.style.configure("CardTitle.TLabel", background=self.colors["bg_dark"], foreground=self.colors["text_light"], font=("Segoe UI", 10, "bold"))
        self.style.configure("CardHint.TLabel", background=self.colors["bg_dark"], foreground=self.colors["text_dark"], font=("Segoe UI", 9))
        self.style.map(
            "TButton",
            background=[("active", self.colors["primary_dark"]), ("disabled", self.colors["bg_dark"])],
            foreground=[("disabled", "#64748b")],
        )

        self.style.configure(
            "TEntry",
            fieldbackground=self.colors["bg_dark"],
            foreground=self.colors["text_light"],
            insertcolor=self.colors["text_light"],
            bordercolor=self.colors["border"],
            lightcolor=self.colors["border"],
            darkcolor=self.colors["border"],
            padding=6,
        )
        
        # Custom styles for different components
        self.style.configure("Title.TLabel", 
                            font=("Segoe UI", 14, "bold"), 
                            padding=10, 
                            background=self.colors["bg_dark"],
                            foreground=self.colors["text_light"])

        # Button styles
        self.style.configure("Primary.TButton", 
                            font=("Segoe UI", 10),
                    background=self.colors["primary"],
                    foreground=self.colors["text_light"])
        
        self.style.configure("Success.TButton", 
                            font=("Segoe UI", 10),
                    background=self.colors["secondary"],
                    foreground=self.colors["text_light"])
        
        self.style.configure("Danger.TButton", 
                            font=("Segoe UI", 10),
                    background=self.colors["danger"],
                    foreground=self.colors["text_light"])
        self.style.map(
            "Card.TFrame",
            background=[("active", self.colors["bg_light"])],
        )
        
    def create_layout(self):
        """Create the main application layout"""
        # Main container with padding
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # Header frame
        self.header_frame = ttk.Frame(self.main_container)
        self.header_frame.pack(fill=tk.X)
        
        self.app_title = ttk.Label(
            self.header_frame, 
            text="Wallpaper Manager", 
            style="Title.TLabel", 
            anchor="center"
        )
        self.app_title.pack(fill=tk.X)

        self.instructions = ttk.Label(
            self.header_frame,
            text="Click a wallpaper thumbnail to preview the delete prompt.",
            anchor="center",
            padding=(0, 0, 0, 8)
        )
        self.instructions.pack(fill=tk.X)
        
        # Content area with a direct thumbnail gallery
        self.content_frame = ttk.Frame(self.main_container)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.create_gallery()
        
        # Status bar
        self.status_bar = ttk.Label(
            self.main_container,
            text="Ready",
            relief=tk.SUNKEN,
            anchor=tk.W,
            padding=(10, 2)
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Bottom action buttons
        self.create_action_buttons()
        
    def create_gallery(self):
        """Create the scrollable thumbnail gallery."""
        self.gallery_header = ttk.Frame(self.content_frame)
        self.gallery_header.pack(fill=tk.X, pady=(0, 8))

        self.gallery_title = ttk.Label(
            self.gallery_header,
            text="Wallpaper History",
            font=("Segoe UI", 12, "bold"),
            anchor="w",
            padding=5,
        )
        self.gallery_title.pack(side=tk.LEFT)

        self.search_frame = ttk.Frame(self.gallery_header)
        self.search_frame.pack(side=tk.RIGHT)

        self.search_label = ttk.Label(self.search_frame, text="Search:", padding=(5, 0))
        self.search_label.pack(side=tk.LEFT)

        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(self.search_frame, textvariable=self.search_var, width=32)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_var.trace_add("write", self.filter_gallery)

        self.clear_search_btn = ttk.Button(self.search_frame, text="Clear", command=self.clear_search)
        self.clear_search_btn.pack(side=tk.LEFT)

        self.gallery_canvas = tk.Canvas(
            self.content_frame,
            bg=self.colors["bg_light"],
            highlightthickness=1,
            highlightbackground=self.colors["border"]
        )
        self.gallery_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.gallery_scrollbar = ttk.Scrollbar(self.content_frame, orient=tk.VERTICAL, command=self.gallery_canvas.yview)
        self.gallery_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.gallery_canvas.configure(yscrollcommand=self.gallery_scrollbar.set)

        self.gallery_inner = ttk.Frame(self.gallery_canvas)
        self.gallery_window = self.gallery_canvas.create_window((0, 0), window=self.gallery_inner, anchor="nw")

        self.gallery_inner.bind("<Configure>", self.update_gallery_scrollregion)
        self.gallery_canvas.bind("<Configure>", self.resize_gallery_window)
        self.gallery_canvas.bind_all("<MouseWheel>", self.on_mousewheel)
        
    def create_action_buttons(self):
        """Create the action buttons at the bottom of the UI"""
        self.button_frame = ttk.Frame(self.main_container)
        self.button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10, padx=10)
        
        # Keep the footer minimal because the gallery items are the primary controls.
        button_data = [
            ("Refresh List", self.refresh_list, "🔄", "Primary.TButton"),
        ]
        
        # Create buttons with consistent styling
        for text, command, icon, style in button_data:
            btn = ttk.Button(
                self.button_frame, 
                text=f"{icon} {text}", 
                command=command, 
                width=15,
                style=style
            )
            btn.pack(side=tk.LEFT, padx=5)
            
    def initialize_components(self):
        """Set up event bindings for interactive components"""
        self.root.bind("<Configure>", self.schedule_gallery_refresh)
            
    def get_image_cache(self):
        """Retrieve wallpaper image paths from Windows Registry"""
        image_cache = []
        try:
            reg_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop")
            for i in range(winreg.QueryInfoKey(reg_key)[1]):
                name, value, _ = winreg.EnumValue(reg_key, i)
                if "TranscodedImageCache" in name:
                    readable = self.hex_to_ascii(value)
                    path = self.extract_path(readable)
                    if path:
                        image_cache.append(path)
            
            # Update status bar
            self.status_bar.config(text=f"Found {len(image_cache)} wallpapers in history")
        except Exception as e:
            messagebox.showerror("Registry Error", f"Failed to read wallpaper registry: {e}")
            self.status_bar.config(text="Error reading wallpaper history")
        return image_cache

    def hex_to_ascii(self, hex_data):
        """Convert hex data from registry to ASCII string"""
        return ''.join(chr(b) for b in hex_data if b != 0)

    def extract_path(self, data):
        """Extract file path from registry data using regex"""
        match = re.search(r'(.:\\.+?)\\\\', data)
        return match.group(1) if match else None

    def populate_image_list(self):
        """Fill the gallery with wallpaper previews."""
        for child in self.gallery_inner.winfo_children():
            child.destroy()
        self.thumbnail_refs.clear()

        search_text = self.search_var.get().lower().strip()
        visible_paths = []
        for path in self.image_cache:
            if not os.path.exists(path):
                continue
            filename = os.path.basename(path)
            if not search_text or search_text in filename.lower() or search_text in path.lower():
                visible_paths.append(path)

        if not visible_paths:
            empty_state = ttk.Label(
                self.gallery_inner,
                text="No matching wallpapers found.",
                padding=24,
                anchor="center",
            )
            empty_state.grid(row=0, column=0, sticky="nsew")
            self.status_bar.config(text="No wallpapers to display")
            self.update_gallery_scrollregion()
            return

        columns = self.get_gallery_columns()
        for column in range(columns):
            self.gallery_inner.columnconfigure(column, weight=1)

        for index, path in enumerate(visible_paths):
            row = index // columns
            column = index % columns
            self.create_thumbnail_tile(path, row, column)

        self.status_bar.config(text=f"Showing {len(visible_paths)} wallpaper previews")
        self.update_gallery_scrollregion()

    def filter_gallery(self, *args):
        """Filter the wallpaper gallery based on search text."""
        self.populate_image_list()
    
    def clear_search(self):
        """Clear the search box"""
        self.search_var.set("")
        self.populate_image_list()

    def get_gallery_columns(self):
        """Calculate the number of thumbnail columns to show."""
        width = max(self.gallery_canvas.winfo_width(), 1)
        return max(1, width // 230)

    def create_thumbnail_tile(self, image_path, row, column):
        """Create a clickable preview tile for one wallpaper."""
        filename = os.path.basename(image_path)

        tile = ttk.Frame(self.gallery_inner, style="Card.TFrame")
        tile.grid(row=row, column=column, padx=8, pady=8, sticky="nsew")

        preview_size = (180, 120)
        try:
            img = Image.open(image_path)
            img.thumbnail(preview_size, Image.Resampling.LANCZOS)
            thumbnail = ImageTk.PhotoImage(img)
        except Exception:
            fallback = Image.new("RGB", preview_size, self.colors["border"])
            thumbnail = ImageTk.PhotoImage(fallback)

        self.thumbnail_refs[image_path] = thumbnail

        preview_label = ttk.Label(tile, image=thumbnail, style="Card.TLabel")
        preview_label.pack(padx=8, pady=(8, 4))

        title_label = ttk.Label(
            tile,
            text=filename,
            style="CardTitle.TLabel",
            wraplength=190,
            anchor="center",
            justify="center"
        )
        title_label.pack(fill=tk.X, padx=8)

        hint_label = ttk.Label(tile, text="Click to delete", style="CardHint.TLabel", anchor="center")
        hint_label.pack(fill=tk.X, padx=8, pady=(0, 8))

        for widget in (tile, preview_label, title_label, hint_label):
            widget.bind("<Button-1>", lambda event, path=image_path: self.confirm_delete(path))

    def schedule_gallery_refresh(self, event=None):
        """Debounce layout refreshes while the window is resizing."""
        if event is not None and event.widget is not self.root:
            return
        if self.resize_job is not None:
            self.root.after_cancel(self.resize_job)
        self.resize_job = self.root.after(120, self.refresh_gallery_layout)

    def refresh_gallery_layout(self):
        """Rebuild the gallery after a resize so thumbnails stay evenly spaced."""
        self.resize_job = None
        self.populate_image_list()

    def resize_gallery_window(self, event):
        """Keep the inner frame aligned to the canvas width."""
        self.gallery_canvas.itemconfigure(self.gallery_window, width=event.width)

    def update_gallery_scrollregion(self, event=None):
        """Keep the canvas scroll region in sync with the content size."""
        self.gallery_canvas.configure(scrollregion=self.gallery_canvas.bbox("all"))

    def on_mousewheel(self, event):
        """Allow scrolling through the gallery with the mouse wheel."""
        if event.widget == self.gallery_canvas or str(event.widget).startswith(str(self.gallery_canvas)):
            self.gallery_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def confirm_delete(self, image_path):
        """Prompt before deleting a wallpaper from the gallery."""
        if not os.path.exists(image_path):
            messagebox.showerror("File Error", "Wallpaper file not found")
            self.status_bar.config(text="Error: File not found")
            return

        filename = os.path.basename(image_path)
        confirm = messagebox.askyesno(
            "Delete Wallpaper",
            f"Delete this wallpaper?\n\n{filename}",
        )
        if confirm:
            self.delete_wallpaper(image_path)
        
    def get_dominant_color(self, image_path):
        """Get the dominant color from an image to match UI elements"""
        try:
            img = Image.open(image_path)
            img = img.resize((100, 100))  # Resize for faster processing
            img = img.convert('RGB')
            
            # Get all pixels
            pixels = list(img.getdata())
            
            # Count colors
            color_count = {}
            for pixel in pixels:
                if pixel in color_count:
                    color_count[pixel] += 1
                else:
                    color_count[pixel] = 1
            
            # Find dominant color
            dominant_color = max(color_count.items(), key=lambda x: x[1])[0]
            
            # Convert to hex
            hex_color = '#{:02x}{:02x}{:02x}'.format(*dominant_color)
            
            return hex_color
        except:
            return "#3498db"  # Default color on error

    def refresh_list(self):
        """Refresh the wallpaper list from registry"""
        self.image_cache = self.get_image_cache()
        self.populate_image_list()
        self.status_bar.config(text=f"Refreshed wallpaper list - found {len(self.image_cache)} items")

    def delete_wallpaper(self, image_path):
        """Delete the selected wallpaper file."""
        filename = os.path.basename(image_path)

        try:
            os.remove(image_path)
            if image_path in self.image_cache:
                self.image_cache.remove(image_path)
            self.thumbnail_refs.pop(image_path, None)
            self.populate_image_list()
            self.status_bar.config(text=f"Deleted: {filename}")
        except Exception as e:
            messagebox.showerror("Delete Error", f"Failed to delete file: {e}")
            self.status_bar.config(text="Error deleting file")

    def show_tooltip(self, message):
        """Display a temporary tooltip message"""
        tooltip = tk.Toplevel(self.root)
        tooltip.wm_overrideredirect(True)
        tooltip.geometry(f"+{self.root.winfo_rootx() + 50}+{self.root.winfo_rooty() + 50}")
        
        # Style the tooltip
        tooltip_frame = ttk.Frame(tooltip)
        tooltip_frame.pack(fill=tk.BOTH, expand=True)
        
        tooltip_frame.configure(style="TFrame")
        
        # Add a border and background color
        tooltip_label = ttk.Label(
            tooltip_frame, 
            text=message,
            font=("Segoe UI", 11),
            padding=10,
            background=self.colors["primary"],
            foreground=self.colors["text_light"]
        )
        tooltip_label.pack()
        
        # Auto-close tooltip after delay
        self.root.after(1500, tooltip.destroy)


if __name__ == "__main__":
    root = tk.Tk()
    app = WallpaperManager(root)
    root.mainloop()