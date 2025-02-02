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

def scan_system_for_git_repos():
    # Get all disk drives (Unix-like systems)
    if os.name == 'posix':
        drives = ['/']
    elif os.name == 'nt':
        drives = [f"{d}:\\" for d in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' if os.path.exists(f"{d}:\\")]
    else:
        print("Unsupported OS")
        return

    all_emails = set()
    for drive in drives:
        print(f"Scanning {drive} for Git repositories...")
        git_repos = find_git_repos(drive)
        print(f"Found {len(git_repos)} Git repositories in {drive}.")
        
        for repo in git_repos:
            print(f"Extracting emails from {repo}...")
            emails = extract_emails_from_repo(repo)
            all_emails.update(emails)
    
    print("\nUnique email addresses found:")
    for email in sorted(all_emails):
        print(email)

if __name__ == "__main__":
    scan_system_for_git_repos()