import os
import tkinter as tk
from tkinter import ttk, messagebox
import winreg
from PIL import Image, ImageTk  # Ensure Pillow is installed: pip install pillow

class WallpaperManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Wallpaper Manager")
        self.root.geometry("800x500")
        self.root.resizable(True, True)

        # Initialize image cache
        self.image_cache = self.get_image_cache()

        # Create left panel for image list
        self.list_frame = ttk.Frame(self.root, width=300)
        self.list_frame.pack(side=tk.LEFT, fill=tk.Y)

        # Create Treeview with a single column
        self.image_list = ttk.Treeview(self.list_frame, columns=("path",), show="headings")
        self.image_list.heading("path", text="Image Path")  # Set the column header
        self.image_list.column("path", width=280)  # Set the column width
        self.image_list.pack(fill=tk.BOTH, expand=True)
        self.image_list.bind("<Double-1>", self.show_in_explorer)
        self.image_list.bind("<<TreeviewSelect>>", self.update_preview)

        # Create right panel for preview
        self.preview_frame = ttk.Frame(self.root)
        self.preview_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.preview_label = ttk.Label(self.preview_frame, text="Preview")
        self.preview_label.pack()

        self.preview_image = tk.Label(self.preview_frame)
        self.preview_image.pack(fill=tk.BOTH, expand=True)

        # Add buttons
        self.button_frame = ttk.Frame(self.root)
        self.button_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.btn_refresh = ttk.Button(self.button_frame, text="Refresh List", command=self.refresh_list)
        self.btn_refresh.pack(side=tk.LEFT, padx=5, pady=5)

        self.btn_explorer = ttk.Button(self.button_frame, text="Show in Explorer", command=self.show_in_explorer)
        self.btn_explorer.pack(side=tk.LEFT, padx=5, pady=5)

        self.btn_delete = ttk.Button(self.button_frame, text="Delete Selected", command=self.delete_selected)
        self.btn_delete.pack(side=tk.LEFT, padx=5, pady=5)

        self.btn_copy = ttk.Button(self.button_frame, text="Copy Path", command=self.copy_path)
        self.btn_copy.pack(side=tk.LEFT, padx=5, pady=5)

        # Populate image list
        self.populate_image_list()

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