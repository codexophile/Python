#!/usr/bin/env python3
import os
import subprocess
import sys
from pathlib import Path

def clean_filename(filename):
    """Clean the filename by removing [tm] prefix and any leading/trailing whitespace"""
    return filename.replace('[tm]', '').strip()

def move_files_between_repos(file_list, source_repo, dest_repo):
    """
    Move files from source repository to destination repository and remove their history
    from the source repository.
    
    Args:
        file_list (list): List of filenames to move
        source_repo (str): Path to source repository
        dest_repo (str): Path to destination repository
    """
    # Clean filenames
    # file_list = [clean_filename(f) for f in file_list]
    
    # Create paths file for git-filter-repo
    paths_file = Path('files_to_remove.txt')
    with open(paths_file, 'w') as f:
        for filename in file_list:
            f.write(f'{filename}\n')
    
    # Copy files to destination repository
    print("Copying files to destination repository...")
    for filename in file_list:
        source_path = Path(source_repo) / filename
        dest_path = Path(dest_repo) / filename
        
        # Create destination directory if it doesn't exist
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            if source_path.exists():
                with open(source_path, 'rb') as src, open(dest_path, 'wb') as dst:
                    dst.write(src.read())
                print(f"Copied: {filename}")
            else:
                print(f"Warning: Source file not found: {filename}")
        except Exception as e:
            print(f"Error copying {filename}: {e}")
    
    # Commit files in destination repository
    print("\nCommitting files in destination repository...")
    subprocess.run(['git', '-C', dest_repo, 'add', '.'], check=True)
    subprocess.run(['git', '-C', dest_repo, 'commit', '-m', 'Add moved files'], check=True)
    
    # Remove files and their history from source repository
    print("\nRemoving files and history from source repository...")
    subprocess.run([
        'git-filter-repo',
        '--invert-paths',
        '--paths-from-file', paths_file,
        '--force'
    ], cwd=source_repo, check=True)
    
    # Clean up
    paths_file.unlink()
    print("\nOperation completed successfully!")

if __name__ == '__main__':
    # Your list of files
    files = """
    [tm] xp.user.js
    [tm] xtapes.user.js
    # ... (rest of your files)
    [tm] xh.user.js
    """.strip().split('\n')
    
    # Get repository paths from command line arguments
    if len(sys.argv) != 3:
        print("Usage: python script.py <source_repo_path> <dest_repo_path>")
        sys.exit(1)
    
    source_repo = sys.argv[1]
    dest_repo = sys.argv[2]
    
    # Execute the move
    move_files_between_repos(files, source_repo, dest_repo)
