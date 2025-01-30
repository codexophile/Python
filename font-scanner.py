import os
from fontTools.ttLib import TTFont
import pyperclip

def get_font_family_names(folder_path):
    font_family_names = set()  # Use a set to avoid duplicates

    # Supported font file extensions
    supported_extensions = ('.ttf', '.otf', '.woff', '.woff2')

    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith(supported_extensions):
                try:
                    font_path = os.path.join(root, file)
                    font = TTFont(font_path)
                    name_table = font['name']
                    
                    # Extract font family name
                    for record in name_table.names:
                        if record.nameID == 1 and record.platformID == 3 and record.platEncID == 1:
                            font_family_names.add(record.toUnicode())
                            break
                except Exception as e:
                    print(f"Error processing {file}: {e}")

    return sorted(font_family_names)  # Sort the names alphabetically

def main():
    folder_path = input("Enter the path to the folder containing font files: ").strip()
    
    if not os.path.isdir(folder_path):
        print("Invalid folder path.")
        return

    font_family_names = get_font_family_names(folder_path)
    result = ", ".join(font_family_names)

    print("\nFont Family Names:")
    print(result)

    copy_to_clipboard = input("\nDo you want to copy the result to the clipboard? (y/n): ").strip().lower()
    if copy_to_clipboard == 'y':
        pyperclip.copy(result)
        print("Result copied to clipboard!")

if __name__ == "__main__":
    main()