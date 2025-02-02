import os
import subprocess
import re

def find_git_repos(root_dir):
    git_repos = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        if '.git' in dirnames:
            git_repos.append(dirpath)
            dirnames[:] = []  # Stop further traversal into this directory
    return git_repos

def extract_emails_from_repo(repo_path):
    try:
        # Run git log to get all commits and extract emails
        result = subprocess.run(
            ['git', 'log', '--pretty=format:%ae'],
            cwd=repo_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode != 0:
            print(f"Error in {repo_path}: {result.stderr}")
            return set()
        
        # Extract unique emails
        emails = set(result.stdout.splitlines())
        return emails
    except Exception as e:
        print(f"Exception in {repo_path}: {e}")
        return set()

def scan_directory_for_git_repos(directory):
    print(f"Scanning {directory} for Git repositories...")
    git_repos = find_git_repos(directory)
    print(f"Found {len(git_repos)} Git repositories in {directory}.")
    
    # Dictionary to store emails and their associated repo paths
    email_repo_map = {}

    for repo in git_repos:
        print(f"Extracting emails from {repo}...")
        emails = extract_emails_from_repo(repo)
        for email in emails:
            if email not in email_repo_map:
                email_repo_map[email] = []
            email_repo_map[email].append(repo)
    
    print("\nEmail addresses and their associated repository paths:")
    for email, repos in sorted(email_repo_map.items()):
        print(f"\nEmail: {email}")
        for repo in repos:
            print(f"  - {repo}")

def scan_system_for_git_repos():
    # Get all disk drives (Unix-like systems)
    if os.name == 'posix':
        drives = ['/']
    elif os.name == 'nt':
        drives = [f"{d}:\\" for d in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' if os.path.exists(f"{d}:\\")]
    else:
        print("Unsupported OS")
        return

    # Dictionary to store emails and their associated repo paths
    email_repo_map = {}

    for drive in drives:
        print(f"Scanning {drive} for Git repositories...")
        git_repos = find_git_repos(drive)
        print(f"Found {len(git_repos)} Git repositories in {drive}.")
        
        for repo in git_repos:
            print(f"Extracting emails from {repo}...")
            emails = extract_emails_from_repo(repo)
            for email in emails:
                if email not in email_repo_map:
                    email_repo_map[email] = []
                email_repo_map[email].append(repo)
    
    print("\nEmail addresses and their associated repository paths:")
    for email, repos in sorted(email_repo_map.items()):
        print(f"\nEmail: {email}")
        for repo in repos:
            print(f"  - {repo}")

def main():
    print("Do you want to scan the entire system or a specific folder?")
    choice = input("Enter 'system' to scan the entire system or 'folder' to scan a specific folder: ").strip().lower()
    
    if choice == 'system':
        scan_system_for_git_repos()
    elif choice == 'folder':
        folder_path = input("Enter the path of the folder to scan: ").strip()
        if os.path.isdir(folder_path):
            scan_directory_for_git_repos(folder_path)
        else:
            print("Invalid folder path. Please provide a valid directory.")
    else:
        print("Invalid choice. Please enter 'system' or 'folder'.")

if __name__ == "__main__":
    main()