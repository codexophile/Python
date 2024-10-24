from PIL import Image
import os

def calculate_brightness(image):
    # Convert image to grayscale
    grayscale_image = image.convert('L')
    # Calculate average pixel intensity
    histogram = grayscale_image.histogram()
    pixels = sum(histogram)
    brightness = sum(index * value for index, value in enumerate(histogram)) / pixels
    return brightness

def separate_images_by_brightness(folder_path, threshold=100):
    dark_images_folder = 'dark_images'
    light_images_folder = 'light_images'
    
    os.makedirs(dark_images_folder, exist_ok=True)
    os.makedirs(light_images_folder, exist_ok=True)
    
    for filename in os.listdir(folder_path):
        try:
            image_path = os.path.join(folder_path, filename)
            image = Image.open(image_path)
            brightness = calculate_brightness(image)
            
            if brightness < threshold:
                os.rename(image_path, os.path.join(dark_images_folder, filename))
            else:
                os.rename(image_path, os.path.join(light_images_folder, filename))
        
        except Exception as e:
            print(f"Error processing {filename}: {str(e)}")

# Example usage
folder_path = 'D:\Images\Wallpapers'
separate_images_by_brightness(folder_path, threshold=100)
