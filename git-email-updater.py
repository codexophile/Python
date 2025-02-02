#!/usr/bin/env python3
import subprocess
import re
import sys
import argparse
from collections import defaultdict

def get_commit_emails(repo_path):
    """
    Scan a git repository and return all unique email addresses used in commits.
    
    Args:
        repo_path (str): Path to the git repository
        
    Returns:
        dict: Dictionary with emails as keys and their commit counts as values
    """
    try:
        # Change to repository directory
        subprocess.run(['git', '-C', repo_path, 'rev-parse'], 
                     check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print(f"Error: {repo_path} is not a valid git repository")
        sys.exit(1)

    # Get all commits with author emails
    result = subprocess.run(
        ['git', '-C', repo_path, 'log', '--format=%ae'],
        capture_output=True,
        text=True
    )
    
    # Count email occurrences
    emails = defaultdict(int)
    for email in result.stdout.strip().split('\n'):
        if email:  # Skip empty lines
            emails[email] += 1
            
    return emails

def update_commit_emails(repo_path, old_email, new_email):
    """
    Update all commits from a specific email address to use a new email address.
    
    Args:
        repo_path (str): Path to the git repository
        old_email (str): Email address to replace
        new_email (str): New email address to use
    """
    # Create the filter-branch command
    git_filter = f'''
if [ "$GIT_AUTHOR_EMAIL" = "{old_email}" ];
then
    export GIT_AUTHOR_EMAIL="{new_email}";
fi
if [ "$GIT_COMMITTER_EMAIL" = "{old_email}" ];
then
    export GIT_COMMITTER_EMAIL="{new_email}";
fi
'''
    
    try:
        # Remove any existing filter-branch backup
        subprocess.run(['git', '-C', repo_path, 'filter-branch', '-f', '--env-filter', git_filter, '--tag-name-filter', 'cat', '--', '--all'],
                      check=True, capture_output=True)
        print(f"\nSuccessfully updated all commits from {old_email} to {new_email}")
        print("\nNote: This operation has rewritten git history. If this is a shared repository,")
        print("you will need to force push the changes and other contributors will need to rebase.")
        
    except subprocess.CalledProcessError as e:
        print(f"Error updating commits: {e.stderr.decode()}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='Git repository email scanner and updater')
    parser.add_argument('repo_path', help='Path to the git repository')
    args = parser.parse_args()
    
    # Get and display all emails
    emails = get_commit_emails(args.repo_path)
    
    if not emails:
        print("No commits found in the repository")
        sys.exit(0)
        
    print("\nEmails found in repository commits:")
    for email, count in emails.items():
        print(f"{email}: {count} commit(s)")
    
    # Ask if user wants to update emails
    response = input("\nWould you like to update any email addresses? (y/n): ").lower()
    
    if response == 'y':
        old_email = input("\nEnter the email address to replace: ").strip()
        if old_email not in emails:
            print(f"Error: Email address {old_email} not found in repository")
            sys.exit(1)
            
        new_email = input("Enter the new email address: ").strip()
        if not re.match(r"[^@]+@[^@]+\.[^@]+", new_email):
            print("Error: Invalid email format")
            sys.exit(1)
            
        # Confirm before proceeding
        confirm = input(f"\nThis will replace all instances of {old_email} with {new_email}.\nThis action cannot be undone. Continue? (y/n): ").lower()
        if confirm == 'y':
            update_commit_emails(args.repo_path, old_email, new_email)
        else:
            print("Operation cancelled")
    
if __name__ == "__main__":
    main()
