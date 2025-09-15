import sys
import tldextract
from collections import defaultdict
import pyperclip
import tkinter as tk
from tkinter import filedialog

def group_urls_from_file(input_filename):
    """Reads a OneTab export file, groups URLs by domain, and returns the formatted text."""
    
    # --- Robust file reading with multiple encodings ---
    encodings_to_try = ['utf-8', 'cp1252', 'latin-1']
    correct_encoding = None

    for encoding in encodings_to_try:
        try:
            # Try to open and read the file to test the encoding
            with open(input_filename, 'r', encoding=encoding) as f:
                f.read() # Read the whole file to ensure there are no hidden errors
            correct_encoding = encoding
            print(f"✅ File successfully read using '{correct_encoding}' encoding.")
            break # Found a working encoding, so we can stop looping
        except UnicodeDecodeError:
            # This encoding failed, so the loop will continue to the next one
            continue
        except FileNotFoundError:
            print(f"❌ ERROR: The file '{input_filename}' was not found.")
            sys.exit(1)
        except Exception as e:
            print(f"❌ An unexpected error occurred: {e}")
            sys.exit(1)

    if not correct_encoding:
        print(f"❌ ERROR: Could not decode the file using any of the tried encodings: {encodings_to_try}")
        print("The file may be corrupted or in an unsupported format.")
        sys.exit(1)
        
    # --- Now process the file using the determined correct encoding ---
    grouped_urls = defaultdict(list)
    try:
        with open(input_filename, 'r', encoding=correct_encoding) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                url_part = line.split(' | ')[0]
                extracted = tldextract.extract(url_part)
                domain = extracted.registered_domain
                
                if not domain:
                    domain = "other_or_local"

                grouped_urls[domain].append(line)
    except Exception as e:
        print(f"❌ An error occurred during URL processing: {e}")
        sys.exit(1)

    # --- Format the output string ---
    output_lines = []
    for domain in sorted(grouped_urls.keys()):
        output_lines.append(f"\n{domain} | --- {domain} ({len(grouped_urls[domain])} links) ---\n")
        for link in sorted(grouped_urls[domain]):
            output_lines.append(link)
            
    if output_lines:
        output_lines[0] = output_lines[0].lstrip()
        
    return "\n".join(output_lines)

def main():
    """Main function to orchestrate the script's execution."""
    if len(sys.argv) < 2:
        print("Usage: python sort_tabs.py <path_to_your_onetab_file.txt>")
        sys.exit(1)
        
    input_file = sys.argv[1]
    print(f"Processing '{input_file}'...")

    organized_text = group_urls_from_file(input_file)
    
    if not organized_text:
        print("No URLs found or processed. Exiting.")
        return

    try:
        pyperclip.copy(organized_text)
        print("✅ Success! Organized URLs have been copied to your clipboard.")
    except pyperclip.PyperclipException:
        print("⚠️ Warning: Could not copy to clipboard. (On Linux, try: sudo apt-get install xclip)")

    print("Opening 'Save As' dialog...")
    try:
        root = tk.Tk()
        root.withdraw()
        filepath = filedialog.asksaveasfilename(
            title="Save the grouped URLs as...",
            defaultextension=".txt",
            # We now save as UTF-8 by default for maximum compatibility
            initialfile="grouped_urls.txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        
        if filepath:
            # Always write the output as UTF-8, the modern standard
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(organized_text)
            print(f"✅ File successfully saved to: {filepath}")
        else:
            print("ℹ️ Save operation was cancelled by the user.")
            
    except Exception as e:
        print(f"❌ An error occurred with the save dialog or file writing: {e}")

if __name__ == "__main__":
    main()