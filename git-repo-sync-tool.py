import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import shutil
import git
import threading
import time
from tkinterdnd2 import DND_FILES, TkinterDnD

# Use a wrapper class to make customtkinter compatible with tkinterdnd2
class Tk(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)

class App(Tk):
    def __init__(self):
        super().__init__()

        # --- Window Setup ---
        self.title("Git Repo Re-Sync Tool")
        self.geometry("700x550")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)
        
        ctk.set_appearance_mode("System")
        
        # --- Widgets ---
        # Frame for inputs
        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.input_frame.grid_columnconfigure(1, weight=1)

        # Local Folder Path
        self.folder_label = ctk.CTkLabel(self.input_frame, text="Local Folder:")
        self.folder_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.folder_entry = ctk.CTkEntry(self.input_frame, placeholder_text="Drag & drop your local project folder here, or paste the path")
        self.folder_entry.grid(row=0, column=1, padx=(0, 5), pady=5, sticky="ew")
        self.browse_button = ctk.CTkButton(self.input_frame, text="Browse...", width=80, command=self.browse_folder)
        self.browse_button.grid(row=0, column=2, padx=(0, 10), pady=5)

        # GitHub Repo URL
        self.url_label = ctk.CTkLabel(self.input_frame, text="GitHub URL:")
        self.url_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.url_entry = ctk.CTkEntry(self.input_frame, placeholder_text="Drag & drop the repo link from your browser here, or paste the URL")
        self.url_entry.grid(row=1, column=1, columnspan=2, padx=(0, 10), pady=5, sticky="ew")

        # Branch Name
        self.branch_label = ctk.CTkLabel(self.input_frame, text="Branch Name:")
        self.branch_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.branch_entry = ctk.CTkEntry(self.input_frame)
        self.branch_entry.insert(0, "main") # Default to main
        self.branch_entry.grid(row=2, column=1, columnspan=2, padx=(0,10), pady=5, sticky="w")


        # Sync Button
        self.sync_button = ctk.CTkButton(self, text="Start Re-Sync Process", command=self.start_sync_thread)
        self.sync_button.grid(row=1, column=0, padx=10, pady=10)
        
        # Cleanup Checkbox
        self.cleanup_var = tk.BooleanVar(value=False)
        self.cleanup_check = ctk.CTkCheckBox(self, text="Delete backup folder after successful sync", variable=self.cleanup_var)
        self.cleanup_check.grid(row=2, column=0, padx=10, pady=5, sticky="w")

        # Log/Status Textbox
        self.log_textbox = ctk.CTkTextbox(self, state="disabled", wrap="word")
        self.log_textbox.grid(row=3, column=0, padx=10, pady=10, sticky="nsew")

        # --- Drag and Drop Setup ---
        self.folder_entry.drop_target_register(DND_FILES)
        self.folder_entry.dnd_bind('<<Drop>>', self.handle_folder_drop)
        self.url_entry.drop_target_register(DND_FILES)
        self.url_entry.dnd_bind('<<Drop>>', self.handle_url_drop)

        self.log_message("Welcome! Provide your folder and URL to begin.", "blue")

    def log_message(self, message, color="white"):
        """Thread-safe logging to the textbox."""
        self.log_textbox.configure(state="normal")
        # Create a tag for color if it doesn't exist
        self.log_textbox.tag_config(color, foreground=color)
        self.log_textbox.insert("end", f"{message}\n", color)
        self.log_textbox.configure(state="disabled")
        self.log_textbox.see("end") # Auto-scroll
        self.update_idletasks()

    def browse_folder(self):
        """Opens a dialog to select a folder."""
        path = filedialog.askdirectory()
        if path:
            self.folder_entry.delete(0, "end")
            self.folder_entry.insert(0, path)

    def handle_folder_drop(self, event):
        """Handles dropping a folder onto the entry."""
        # The path might be enclosed in curly braces {}
        path = event.data.strip('{}')
        self.folder_entry.delete(0, "end")
        self.folder_entry.insert(0, path)
        return event.action

    def handle_url_drop(self, event):
        """Handles dropping a URL onto the entry."""
        url = event.data.strip()
        self.url_entry.delete(0, "end")
        self.url_entry.insert(0, url)
        return event.action

    def start_sync_thread(self):
        """Starts the sync process in a separate thread to keep the GUI responsive."""
        local_path = self.folder_entry.get().strip()
        repo_url = self.url_entry.get().strip()
        branch_name = self.branch_entry.get().strip()

        if not local_path or not os.path.isdir(local_path):
            messagebox.showerror("Error", "The provided local path is not a valid folder.")
            return
        if not repo_url or not repo_url.endswith(".git"):
            messagebox.showerror("Error", "Please provide a valid Git repository URL (ending in .git).")
            return
        if not branch_name:
            messagebox.showerror("Error", "Branch name cannot be empty.")
            return

        self.sync_button.configure(state="disabled", text="Syncing...")
        
        # Run the core logic in a thread
        thread = threading.Thread(target=self.run_sync_logic, args=(local_path, repo_url, branch_name))
        thread.daemon = True
        thread.start()

    def run_sync_logic(self, local_path, repo_url, branch_name):
        """The core logic for re-syncing the repository."""
        try:
            self.log_message("\n" + "="*50, "gray")
            self.log_message(f"Starting process for: {os.path.basename(local_path)}", "lightblue")

            # 1. Backup the current folder
            parent_dir = os.path.dirname(local_path)
            repo_name = os.path.basename(local_path)
            backup_path = os.path.join(parent_dir, f"{repo_name}-backup-{int(time.time())}")
            self.log_message(f"Backing up '{local_path}' to '{backup_path}'...")
            shutil.move(local_path, backup_path)

            # 2. Clone the fresh repository
            self.log_message(f"Cloning fresh repo from {repo_url}...")
            cloned_repo = git.Repo.clone_from(repo_url, local_path, branch=branch_name)
            
            # 3. Sync files from backup to new clone
            self.log_message("Syncing your latest code into the new repository...")
            
            # Delete old files in the clone (except .git)
            for item in os.listdir(local_path):
                if item == ".git":
                    continue
                item_path = os.path.join(local_path, item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
            
            # Copy new files from backup
            for item in os.listdir(backup_path):
                source_item = os.path.join(backup_path, item)
                dest_item = os.path.join(local_path, item)
                if os.path.isdir(source_item):
                    shutil.copytree(source_item, dest_item)
                else:
                    shutil.copy2(source_item, dest_item)

            self.log_message("File sync complete.")

            # 4. Commit and Push
            if not cloned_repo.is_dirty(untracked_files=True):
                self.log_message("No changes detected. The remote repo might already be up to date.", "yellow")
            else:
                self.log_message("Staging all changes...")
                cloned_repo.git.add(A=True)
                
                self.log_message("Committing changes...")
                commit_message = "Automated Restore: Sync local changes after .git deletion"
                cloned_repo.index.commit(commit_message)
                
                self.log_message(f"Pushing changes to origin/{branch_name}...")
                origin = cloned_repo.remote(name='origin')
                origin.push()

            # 5. Cleanup
            if self.cleanup_var.get():
                self.log_message(f"Cleaning up backup folder: {backup_path}", "gray")
                shutil.rmtree(backup_path)
            else:
                self.log_message(f"Backup preserved at: {backup_path}", "yellow")

            self.log_message("SUCCESS: Repository re-synced successfully!", "lightgreen")

        except git.GitCommandError as e:
            self.log_message(f"GIT ERROR: {e}", "red")
            messagebox.showerror("Git Error", f"An error occurred during a Git command:\n\n{e}\n\nCheck your URL, branch name, and permissions.")
        except Exception as e:
            self.log_message(f"UNEXPECTED ERROR: {e}", "red")
            messagebox.showerror("Unexpected Error", f"An unexpected error occurred:\n\n{e}")
        finally:
            # Re-enable the button in the main thread
            self.after(0, self.sync_button.configure, {"state": "normal", "text": "Start Re-Sync Process"})

if __name__ == "__main__":
    app = App()
    app.mainloop()