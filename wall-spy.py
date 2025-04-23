import os
import tkinter as tk
from tkinter import ttk, messagebox
import winreg
from PIL import Image, ImageTk  # Ensure Pillow is installed: pip install pillow

class WallpaperManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Wallpaper Manager")
        self.root.geometry("1000x600")
        self.root.minsize(800, 500)
        
        # Configure the style
        self.style = ttk.Style()
        self.style.configure("Treeview", rowheight=25)
        self.style.configure("Custom.TFrame", background="#f5f5f5")
        self.style.configure("Title.TLabel", font=("Segoe UI", 12, "bold"), padding=10)
        self.style.configure("Preview.TLabel", font=("Segoe UI", 11), padding=5)
        
        # Main container with padding
        self.main_container = ttk.Frame(self.root, padding="10")
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # Initialize image cache
        self.image_cache = self.get_image_cache()
        
        # Create left panel with title
        self.list_frame = ttk.Frame(self.main_container, style="Custom.TFrame")
        self.list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # List title
        self.list_title = ttk.Label(self.list_frame, text="Wallpaper History", style="Title.TLabel")
        self.list_title.pack(fill=tk.X)
        
        # Create Treeview with scrollbar
        self.tree_frame = ttk.Frame(self.list_frame)
        self.tree_frame.pack(fill=tk.BOTH, expand=True)
        
        self.scrollbar = ttk.Scrollbar(self.tree_frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.image_list = ttk.Treeview(self.tree_frame, columns=("path",), show="headings",
                                      yscrollcommand=self.scrollbar.set)
        self.image_list.heading("path", text="Image Path")
        self.image_list.column("path", width=280)
        self.image_list.pack(fill=tk.BOTH, expand=True)
        
        self.scrollbar.config(command=self.image_list.yview)
        
        # Bind events
        self.image_list.bind("<Double-1>", self.show_in_explorer)
        self.image_list.bind("<<TreeviewSelect>>", self.update_preview)
        
        # Create right panel for preview
        self.preview_frame = ttk.Frame(self.main_container, style="Custom.TFrame")
        self.preview_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.preview_title = ttk.Label(self.preview_frame, text="Preview", style="Title.TLabel")
        self.preview_title.pack(fill=tk.X)
        
        self.preview_container = ttk.Frame(self.preview_frame, style="Custom.TFrame")
        self.preview_container.pack(fill=tk.BOTH, expand=True)
        
        self.preview_image = ttk.Label(self.preview_container)
        self.preview_image.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Button frame with modern styling
        self.button_frame = ttk.Frame(self.main_container, style="Custom.TFrame")
        self.button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))
        
        # Create buttons with consistent padding and spacing
        button_data = [
            ("Refresh List", self.refresh_list, "⟳"),
            ("Show in Explorer", self.show_in_explorer, "📂"),
            ("Delete Selected", self.delete_selected, "🗑"),
            ("Copy Path", self.copy_path, "📋")
        ]
        
        for text, command, icon in button_data:
            btn = ttk.Button(self.button_frame, text=f"{icon} {text}", command=command, width=15)
            btn.pack(side=tk.LEFT, padx=5)
        
        # Populate image list
        self.populate_image_list()
        
        # Configure grid weights
        self.main_container.columnconfigure(0, weight=1)
        self.main_container.columnconfigure(1, weight=1)

    def update_preview(self, event=None):
        selected_item = self.image_list.selection()
        if selected_item:
            image_path = self.image_list.item(selected_item, "values")[0]
            try:
                img = Image.open(image_path)
                # Calculate aspect ratio for resizing
                display_size = (400, 400)
                img.thumbnail(display_size, Image.Resampling.LANCZOS)
                img_tk = ImageTk.PhotoImage(img)
                self.preview_image.config(image=img_tk)
                self.preview_image.image = img_tk
            except Exception as e:
                self.preview_image.config(image="")
                messagebox.showerror("Error", f"Failed to load image: {e}")

    def show_tooltip(self, message):
        tooltip = tk.Toplevel(self.root)
        tooltip.wm_overrideredirect(True)
        tooltip.geometry(f"+{self.root.winfo_rootx() + 50}+{self.root.winfo_rooty() + 50}")
        
        # Style the tooltip
        tooltip_frame = ttk.Frame(tooltip, style="Custom.TFrame")
        tooltip_frame.pack(fill=tk.BOTH, expand=True)
        
        label = ttk.Label(tooltip_frame, text=message, style="Preview.TLabel")
        label.pack(padx=10, pady=5)
        
        self.root.after(1500, tooltip.destroy)

    def get_image_cache(self): return self.get_image_cache
    def hex_to_ascii(self, hex_data): return self.hex_to_ascii
    def extract_path(self, data): return self.extract_path
    def populate_image_list(self): return self.populate_image_list
    def show_in_explorer(self, event=None): return self.show_in_explorer
    def refresh_list(self): return self.refresh_list
    def delete_selected(self): return self.delete_selected
    def copy_path(self): return self.copy_path

    def get_image_cache(self):
        image_cache = []
        try:
            reg_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop")
            for i in range(winreg.QueryInfoKey(reg_key)[1]):
                name, value, _ = winreg.EnumValue(reg_key, i)
                if "TranscodedImageCache" in name:
                    readable = self.hex_to_ascii(value)
                    match = self.extract_path(readable)
                    if match:
                        image_cache.append(match)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read registry: {e}")
        return image_cache

    def hex_to_ascii(self, hex_data):
        return ''.join(chr(b) for b in hex_data if b != 0)

    def extract_path(self, data):
        import re
        match = re.search(r'(.:\\.+?)\\\\', data)
        return match.group(1) if match else None

    def populate_image_list(self):
        self.image_list.delete(*self.image_list.get_children())
        for path in self.image_cache:
            self.image_list.insert("", "end", values=(path,))

    def update_preview(self, event=None):
        selected_item = self.image_list.selection()
        if selected_item:
            image_path = self.image_list.item(selected_item, "values")[0]
            try:
                img = Image.open(image_path)
                img.thumbnail((400, 400))
                img_tk = ImageTk.PhotoImage(img)
                self.preview_image.config(image=img_tk)
                self.preview_image.image = img_tk  # Keep a reference to avoid garbage collection
            except Exception as e:
                self.preview_image.config(image="")
                messagebox.showerror("Error", f"Failed to load image: {e}")

    def show_in_explorer(self, event=None):
        selected_item = self.image_list.selection()
        if selected_item:
            image_path = self.image_list.item(selected_item, "values")[0]
            if os.path.exists(image_path):
                os.startfile(os.path.dirname(image_path))
            else:
                messagebox.showerror("Error", "File not found")

    def refresh_list(self):
        self.image_cache = self.get_image_cache()
        self.populate_image_list()

    def delete_selected(self):
        selected_item = self.image_list.selection()
        if selected_item:
            image_path = self.image_list.item(selected_item, "values")[0]
            try:
                os.remove(image_path)
                self.image_list.delete(selected_item)
                self.image_cache = self.get_image_cache()
                self.preview_image.config(image="")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete file: {e}")

    def copy_path(self):
        selected_item = self.image_list.selection()
        if selected_item:
            image_path = self.image_list.item(selected_item, "values")[0]
            self.root.clipboard_clear()
            self.root.clipboard_append(image_path)
            self.root.update()
            self.show_tooltip("Path copied to clipboard!")

    def show_tooltip(self, message):
        tooltip = tk.Toplevel(self.root)
        tooltip.wm_overrideredirect(True)
        tooltip.geometry(f"+{self.root.winfo_rootx() + 50}+{self.root.winfo_rooty() + 50}")
        label = ttk.Label(tooltip, text=message)
        label.pack()
        self.root.after(1000, tooltip.destroy)

if __name__ == "__main__":
    root = tk.Tk()
    app = WallpaperManager(root)
    root.mainloop()