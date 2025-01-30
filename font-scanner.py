import os
from fontTools.ttLib import TTFont
import pyperclip
import re

def clean_font_name(font_name):
    # Remove common variation suffixes (e.g., "Light", "Bold", "Medium", etc.)
    variations = [
        "Light", "Medium", "Bold", "SemiBold", "ExtraBold", "ExtraLight", "Thin", 
        "Retina", "Oblique", "NL", "XLight", "SmBld", "ExtLt", "Text", "Book"
    ]
    for variation in variations:
        font_name = re.sub(rf"\s*{variation}\s*", "", font_name, flags=re.IGNORECASE)
    return font_name.strip()

def get_main_font_names(folder_path):
    main_font_names = set()  # Use a set to avoid duplicates

    # Supported font file extensions
    supported_extensions = ('.ttf', '.otf', '.woff', '.woff2')

    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith(supported_extensions):
                try:
                    font_path = os.path.join(root, file)
                    font = TTFont(font_path)
                    name_table = font['name']
                    
                    # Extract the main font family name (nameID = 1)
                    for record in name_table.names:
                        if record.nameID == 1 and record.platformID == 3 and record.platEncID == 1:
                            font_name = record.toUnicode()
                            cleaned_name = clean_font_name(font_name)
                            main_font_names.add(cleaned_name)
                            break
                except Exception as e:
                    print(f"Error processing {file}: {e}")

    return sorted(main_font_names)  # Sort the names alphabetically

def main():
    folder_path = input("Enter the path to the folder containing font files: ").strip()
    
    if not os.path.isdir(folder_path):
        print("Invalid folder path.")
        return

    main_font_names = get_main_font_names(folder_path)
    result = ", ".join(main_font_names)

    print("\nMain Font Family Names (cleaned):")
    print(result)

    copy_to_clipboard = input("\nDo you want to copy the result to the clipboard? (y/n): ").strip().lower()
    if copy_to_clipboard == 'y':
        pyperclip.copy(result)
        print("Result copied to clipboard!")

if __name__ == "__main__":
  os.system('cls')
  main()