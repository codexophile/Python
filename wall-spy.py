import os
import re
import tkinter as tk
from tkinter import ttk, messagebox
import winreg
from PIL import Image, ImageTk
import colorsys


class WallpaperManager:
    """Main application class for managing Windows wallpaper history"""
    
    def __init__(self, root):
        """Initialize the application with UI components and event bindings"""
        self.root = root
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
        self.root.minsize(900, 600)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Set window icon
        try:
            self.root.iconbitmap("wallpaper.ico")
        except:
            pass  # Ignore if icon file isn't available
    
    def setup_colors(self):
        """Define color scheme for the application"""
        # Modern color palette
        self.colors = {
            "primary": "#3498db",       # Blue
            "primary_dark": "#2980b9",  # Darker blue
            "secondary": "#2ecc71",     # Green for positive actions
            "danger": "#e74c3c",        # Red for delete actions
            "neutral": "#95a5a6",       # Gray for normal buttons
            "bg_light": "#f5f7fa",      # Light background
            "bg_dark": "#34495e",       # Dark background
            "text_light": "#ecf0f1",    # Light text
            "text_dark": "#2c3e50",     # Dark text
            "border": "#bdc3c7",        # Border color
        }
        
    def configure_styles(self):
        """Set up custom styles for UI components"""
        self.style = ttk.Style()
        
        # Configure basic styles
        self.style.configure("TFrame", background=self.colors["bg_light"])
        self.style.configure("TLabel", background=self.colors["bg_light"], foreground=self.colors["text_dark"])
        self.style.configure("TButton", background=self.colors["neutral"], padding=5)
        
        # Custom styles for different components
        self.style.configure("Title.TLabel", 
                            font=("Segoe UI", 14, "bold"), 
                            padding=10, 
                            background=self.colors["primary"],
                            foreground=self.colors["text_light"])
        
        self.style.configure("Preview.TLabel", 
                            font=("Segoe UI", 11), 
                            padding=5)
        
        # Button styles
        self.style.configure("Primary.TButton", 
                            font=("Segoe UI", 10),
                            background=self.colors["primary"])
        
        self.style.configure("Success.TButton", 
                            font=("Segoe UI", 10),
                            background=self.colors["secondary"])
        
        self.style.configure("Danger.TButton", 
                            font=("Segoe UI", 10),
                            background=self.colors["danger"])
        
        # Treeview styling
        self.style.configure("Treeview", 
                            rowheight=30,
                            background=self.colors["bg_light"],
                            fieldbackground=self.colors["bg_light"],
                            font=("Segoe UI", 10))
        
        self.style.configure("Treeview.Heading", 
                            font=("Segoe UI", 11, "bold"),
                            background=self.colors["primary"],
                            foreground=self.colors["text_light"])
        
        # Configure hover and selection colors
        self.style.map("Treeview",
                    background=[("selected", self.colors["primary"])],
                    foreground=[("selected", self.colors["text_light"])])
        
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
        
        # Content area with horizontal split
        self.content_frame = ttk.Frame(self.main_container)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel for wallpaper list
        self.list_frame = ttk.Frame(self.content_frame)
        self.list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # List header
        self.list_title = ttk.Label(
            self.list_frame, 
            text="Wallpaper History", 
            font=("Segoe UI", 12, "bold"),
            anchor="w",
            padding=5
        )
        self.list_title.pack(fill=tk.X)
        
        # Treeview with scrollbar for wallpaper list
        self.create_wallpaper_list()
        
        # Right panel for image preview
        self.preview_frame = ttk.Frame(self.content_frame)
        self.preview_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        # Preview header
        self.preview_title = ttk.Label(
            self.preview_frame, 
            text="Preview", 
            font=("Segoe UI", 12, "bold"),
            anchor="w",
            padding=5
        )
        self.preview_title.pack(fill=tk.X)
        
        # Container for the preview image with decorative border
        self.preview_container = ttk.Frame(self.preview_frame, style="TFrame")
        self.preview_container.pack(fill=tk.BOTH, expand=True)
        
        # Create canvas for preview with border and drop shadow effect
        self.preview_canvas = tk.Canvas(
            self.preview_container, 
            bg=self.colors["bg_light"],
            highlightthickness=1,
            highlightbackground=self.colors["border"]
        )
        self.preview_canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Label to display the preview image
        self.preview_image = ttk.Label(self.preview_canvas)
        self.preview_canvas.create_window(0, 0, anchor="nw", window=self.preview_image)
        
        # Image info frame (displays details about selected image)
        self.info_frame = ttk.Frame(self.preview_frame)
        self.info_frame.pack(fill=tk.X, pady=5)
        
        self.image_info = ttk.Label(
            self.info_frame,
            text="No wallpaper selected",
            font=("Segoe UI", 9),
            padding=5
        )
        self.image_info.pack(fill=tk.X)
        
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
        
    def create_wallpaper_list(self):
        """Create the treeview component for displaying wallpaper paths"""
        self.tree_frame = ttk.Frame(self.list_frame)
        self.tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # Add search box above treeview
        self.search_frame = ttk.Frame(self.tree_frame)
        self.search_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.search_label = ttk.Label(
            self.search_frame,
            text="🔍 Search:",
            padding=(5, 0)
        )
        self.search_label.pack(side=tk.LEFT)
        
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(
            self.search_frame,
            textvariable=self.search_var,
            width=40
        )
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.search_var.trace_add("write", self.filter_list)
        
        self.clear_search_btn = ttk.Button(
            self.search_frame,
            text="✕",
            width=3,
            command=self.clear_search
        )
        self.clear_search_btn.pack(side=tk.LEFT)
        
        # Treeview container with scrollbar
        self.list_container = ttk.Frame(self.tree_frame)
        self.list_container.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar for treeview
        self.scrollbar = ttk.Scrollbar(self.list_container)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Treeview for wallpaper list with multiple columns
        self.image_list = ttk.Treeview(
            self.list_container, 
            columns=("filename", "path"), 
            show="headings",
            yscrollcommand=self.scrollbar.set
        )
        
        # Configure columns
        self.image_list.heading("filename", text="Filename")
        self.image_list.heading("path", text="Full Path")
        self.image_list.column("filename", width=150)
        self.image_list.column("path", width=350)
        
        self.image_list.pack(fill=tk.BOTH, expand=True)
        
        # Configure scrollbar to work with treeview
        self.scrollbar.config(command=self.image_list.yview)
        
    def create_action_buttons(self):
        """Create the action buttons at the bottom of the UI"""
        self.button_frame = ttk.Frame(self.main_container)
        self.button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10, padx=10)
        
        # Define button data: (text, command, icon, style)
        button_data = [
            ("Refresh List", self.refresh_list, "🔄", "Primary.TButton"),
            ("Show in Explorer", self.show_in_explorer, "📂", "Primary.TButton"),
            ("Copy Path", self.copy_path, "📋", "Primary.TButton"),
            ("Set as Wallpaper", self.set_as_wallpaper, "🖼️", "Success.TButton"),
            ("Delete Selected", self.delete_selected, "🗑️", "Danger.TButton")
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
        # Double-click to open in explorer
        self.image_list.bind("<Double-1>", self.show_in_explorer)
        # Selection to update preview
        self.image_list.bind("<<TreeviewSelect>>", self.update_preview)
        # Right-click context menu
        self.create_context_menu()
        
    def create_context_menu(self):
        """Create right-click context menu for the image list"""
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Preview", command=self.update_preview)
        self.context_menu.add_command(label="Show in Explorer", command=self.show_in_explorer)
        self.context_menu.add_command(label="Copy Path", command=self.copy_path)
        self.context_menu.add_command(label="Set as Wallpaper", command=self.set_as_wallpaper)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Delete", command=self.delete_selected)
        
        # Bind right-click to show context menu
        self.image_list.bind("<Button-3>", self.show_context_menu)
        
    def show_context_menu(self, event):
        """Display context menu at mouse position"""
        try:
            # Select the item under cursor
            item = self.image_list.identify_row(event.y)
            if item:
                self.image_list.selection_set(item)
                self.update_preview()
                self.context_menu.post(event.x_root, event.y_root)
        except:
            pass
            
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
        """Fill the treeview with wallpaper paths"""
        # Clear existing items
        self.image_list.delete(*self.image_list.get_children())
        
        # Add paths to treeview
        for path in self.image_cache:
            if os.path.exists(path):
                filename = os.path.basename(path)
                self.image_list.insert("", "end", values=(filename, path))
    
    def filter_list(self, *args):
        """Filter the wallpaper list based on search text"""
        search_text = self.search_var.get().lower()
        
        # Clear the current list
        self.image_list.delete(*self.image_list.get_children())
        
        # Add matching items back
        for path in self.image_cache:
            if os.path.exists(path):
                filename = os.path.basename(path)
                if search_text in filename.lower() or search_text in path.lower():
                    self.image_list.insert("", "end", values=(filename, path))
    
    def clear_search(self):
        """Clear the search box"""
        self.search_var.set("")
        
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

    def update_preview(self, event=None):
        """Update the preview image when a wallpaper is selected"""
        selected_item = self.image_list.selection()
        if selected_item:
            # Get file information
            item_values = self.image_list.item(selected_item, "values")
            filename = item_values[0]
            image_path = item_values[1]
            
            try:
                # Get file information
                file_size = os.path.getsize(image_path) / (1024 * 1024)  # Convert to MB
                
                # Open and resize the image for preview
                img = Image.open(image_path)
                img_width, img_height = img.size
                
                # Update image info
                self.image_info.config(
                    text=f"{filename} | {img_width}x{img_height} | {file_size:.2f} MB"
                )
                
                # Calculate aspect ratio for resizing
                preview_width = self.preview_canvas.winfo_width() - 20
                preview_height = self.preview_canvas.winfo_height() - 20
                
                if preview_width < 10:  # Not yet fully rendered
                    preview_width = 400
                    preview_height = 300
                
                # Resize while maintaining aspect ratio
                img.thumbnail((preview_width, preview_height), Image.Resampling.LANCZOS)
                
                # Convert to Tkinter-compatible image
                img_tk = ImageTk.PhotoImage(img)
                
                # Update preview
                self.preview_image.config(image=img_tk)
                self.preview_image.image = img_tk  # Keep a reference to avoid garbage collection
                
                # Center the image in canvas
                canvas_width = self.preview_canvas.winfo_width()
                canvas_height = self.preview_canvas.winfo_height()
                img_width, img_height = img_tk.width(), img_tk.height()
                
                x_position = (canvas_width - img_width) // 2
                y_position = (canvas_height - img_height) // 2
                
                # Position the image
                self.preview_canvas.create_window(x_position, y_position, anchor="nw", window=self.preview_image)
                
                # Update status
                self.status_bar.config(text=f"Previewing: {filename}")
                
            except Exception as e:
                self.preview_image.config(image="")
                self.image_info.config(text="Error loading preview")
                messagebox.showerror("Preview Error", f"Failed to load image: {e}")
        else:
            # No selection
            self.preview_image.config(image="")
            self.image_info.config(text="No wallpaper selected")

    def show_in_explorer(self, event=None):
        """Open File Explorer to the directory containing the selected wallpaper"""
        selected_item = self.image_list.selection()
        if selected_item:
            image_path = self.image_list.item(selected_item, "values")[1]
            if os.path.exists(image_path):
                os.startfile(os.path.dirname(image_path))
                self.status_bar.config(text=f"Opened folder: {os.path.dirname(image_path)}")
            else:
                messagebox.showerror("File Error", "Wallpaper file not found")
                self.status_bar.config(text="Error: File not found")

    def refresh_list(self):
        """Refresh the wallpaper list from registry"""
        self.image_cache = self.get_image_cache()
        self.populate_image_list()
        self.status_bar.config(text=f"Refreshed wallpaper list - found {len(self.image_cache)} items")

    def delete_selected(self):
        """Delete the selected wallpaper file"""
        selected_item = self.image_list.selection()
        if not selected_item:
            messagebox.showinfo("Selection", "Please select a wallpaper to delete")
            return
            
        filename = self.image_list.item(selected_item, "values")[0]
        image_path = self.image_list.item(selected_item, "values")[1]
        
        confirm = messagebox.askyesno(
            "Confirm Delete", 
            f"Are you sure you want to delete:\n{filename}?"
        )
        
        if confirm:
            try:
                os.remove(image_path)
                self.image_list.delete(selected_item)
                self.preview_image.config(image="")
                self.image_info.config(text="No wallpaper selected")
                self.status_bar.config(text=f"Deleted: {filename}")
                
                # Remove from cache
                if image_path in self.image_cache:
                    self.image_cache.remove(image_path)
                
            except Exception as e:
                messagebox.showerror("Delete Error", f"Failed to delete file: {e}")
                self.status_bar.config(text="Error deleting file")

    def copy_path(self):
        """Copy the selected wallpaper path to clipboard"""
        selected_item = self.image_list.selection()
        if not selected_item:
            messagebox.showinfo("Selection", "Please select a wallpaper to copy its path")
            return
            
        image_path = self.image_list.item(selected_item, "values")[1]
        self.root.clipboard_clear()
        self.root.clipboard_append(image_path)
        self.root.update()
        self.show_tooltip("Path copied to clipboard!")
        self.status_bar.config(text="Path copied to clipboard")
    
    def set_as_wallpaper(self):
        """Set the selected image as desktop wallpaper"""
        selected_item = self.image_list.selection()
        if not selected_item:
            messagebox.showinfo("Selection", "Please select a wallpaper to set")
            return
            
        image_path = self.image_list.item(selected_item, "values")[1]
        filename = self.image_list.item(selected_item, "values")[0]
        
        try:
            import ctypes
            ctypes.windll.user32.SystemParametersInfoW(20, 0, image_path, 3)
            self.show_tooltip("Wallpaper set successfully!")
            self.status_bar.config(text=f"Wallpaper set: {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to set wallpaper: {e}")
            self.status_bar.config(text="Error setting wallpaper")

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