import os
from fontTools.ttLib import TTFont
import pyperclip
import re
import sys

def clean_font_name(font_name):
    # Remove common variation suffixes (e.g., "Light", "Bold", "Medium", etc.)
    # Order from longest/most specific to shortest/most general for greedy removal.
    variations = sorted([
        # Multi-word style/weight descriptors (often with Oblique)
        "Black Oblique", "Bold Oblique", "DemiBold Oblique", "ExtraBlack Oblique",
        "ExtraBold Oblique", "ExtraLight Oblique", "Light Oblique", "Medium Oblique",
        "Regular Oblique", "Thin Oblique",

        # Multi-word style/weight descriptors (ensure space handling if they appear like this)
        "Extra Black", "Extra Bold", "Extra Light",
        "Demi Bold", "Semi Bold",

        # Single, more specific style/weight descriptors
        "ExtraBlack", "ExtraBold", "ExtraLight", "DemiBold", "SemiBold",
        "Retina",  # e.g., Fira Code Retina
        "XLight",  # e.g., Operator Mono XLight

        # Common single-word style/weight descriptors
        "Black", "Bold", "Book", "Light", "Medium", "Oblique", "Regular", "Text", "Thin",

        # Common abbreviations for styles/weights
        "ExtLt",   # e.g., IBM Plex Sans ExtLt -> IBM Plex Sans
        "Medm",    # e.g., IBM Plex Sans Medm -> IBM Plex Sans
        "SmBld",   # e.g., IBM Plex Sans SmBld -> IBM Plex Sans

        # Specific sub-family indicators that you want to strip to get a broader family name
        "NL"       # e.g., JetBrains Mono NL -> JetBrains Mono

        # IMPORTANT: Words like "Mono", "Sans", "Serif", "Code", "Pro", "Trial" are often
        # PART OF THE MAIN FONT FAMILY NAME (NameID 1).
        # Your script correctly extracts NameID 1. So, "Fira Code" is a family, "Annotation Mono" is a family.
        # Including "Code" or "Mono" in this `variations` list would incorrectly shorten these names
        # (e.g., "Fira Code" would become "Fira").
        # Only include terms here if they represent styles/weights or sub-family distinctions
        # that you want to remove from the already extracted family name (NameID 1).
    ], key=len, reverse=True) # Sort by length, longest first

    original_font_name = font_name # For comparison if no changes made
    for variation in variations:
        # The regex \s*{variation}\s* will match the variation word(s)
        # surrounded by zero or more whitespace characters on either side.
        # This handles cases like "FontName Variation", "FontNameVariation", "FontName   Variation  "
        # and removes the variation and surrounding/adjacent spaces.
        font_name = re.sub(rf"\s*\b{re.escape(variation)}\b\s*", " ", font_name, flags=re.IGNORECASE).strip()
        # Using \b for word boundaries makes it safer. Replacing with a single space, then stripping.

    # If stripping variations results in an empty string (e.g. font name was just "Bold")
    # it's better to return the original name or handle as an error.
    # For now, if it becomes empty, it means all parts were considered variations.
    # This scenario is unlikely if NameID 1 is correctly fetched.
    if not font_name:
        return original_font_name # Fallback if stripping removes everything

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
    
    if sys.argv.__len__() > 1:
        folder_path = sys.argv[1]
    else:
        folder_path = os.getcwd()
    
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