from PIL import Image, ImageFilter, ImageDraw, ImageFont
import numpy as np
import argparse


def parse_args():
    parser = argparse.ArgumentParser(description='Generate a screenshot with text overlay')
    parser.add_argument('template_path', help='Path to the template image')
    parser.add_argument('source_path', help='Path to the source image')
    parser.add_argument('output_path', help='Path for the output image')
    parser.add_argument('text', help='Text to overlay on the image')

    return parser.parse_args()


def get_dominant_color(template_path):
    img = Image.open(template_path).convert('RGB')
    # Get colors from image
    colors = img.getcolors(img.size[0] * img.size[1])
    # Sort colors by count
    sorted_colors = sorted(colors, key=lambda x: x[0], reverse=True)
    # Return RGB values of most common color
    return sorted_colors[0][1]

def replace_dominant_color(template_path, source_path, output_path, text):
    # Open base image and replacement image
    base_img = Image.open(template_path).convert('RGB')
    replacement_img = Image.open(source_path).convert('RGB')
    
    # Get the dominant color
    dominant = get_dominant_color(template_path)
    
    # Create mask based on dominant color with a tolerance
    base_array = np.array(base_img)
    dominant_array = np.array(dominant)
    
    # Calculate the color distance for each pixel
    distances = np.sqrt(np.sum((base_array - dominant_array) ** 2, axis=2))
    threshold = 30  # Adjust threshold as needed
    mask = Image.fromarray(np.uint8(distances < threshold) * 255, mode='L')
    
    # Smooth the mask
    #mask = mask.filter(ImageFilter.GaussianBlur(radius=2))
    
    # Get the bounding box of the masked area
    bbox = mask.getbbox()
    if bbox is None:
        print("No dominant color area found.")
        return
    left, upper, right, lower = bbox
    mask_width = right - left
    mask_height = lower - upper
    
    # Resize replacement image to fill the mask area while maintaining aspect ratio
    img_width, img_height = replacement_img.size
    aspect_ratio = img_width / img_height
    mask_aspect_ratio = mask_width / mask_height
    
    if aspect_ratio > mask_aspect_ratio:
        # Replacement image is wider than mask area
        new_height = mask_height
        new_width = int(new_height * aspect_ratio)
    else:
        # Replacement image is taller than mask area
        new_width = mask_width
        new_height = int(new_width / aspect_ratio)
    
    resized_replacement = replacement_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # Calculate offsets to center the image within the mask area
    crop_left = (new_width - mask_width) // 2
    crop_upper = (new_height - mask_height) // 2
    crop_right = crop_left + mask_width
    crop_lower = crop_upper + mask_height
    
    # Crop the resized image to the mask dimensions
    cropped_replacement = resized_replacement.crop((crop_left, crop_upper, crop_right, crop_lower))
    
    # Create an image to hold the cropped replacement image at the correct position
    new_replacement_img = Image.new('RGB', base_img.size)
    new_replacement_img.paste(cropped_replacement, (left, upper))
    
    # Composite images using the smoothed mask
    result = Image.composite(new_replacement_img, base_img, mask)
    
    draw = ImageDraw.Draw(result)
    
    font_size = 128  # Adjust as needed
    font_path = '/Library/Fonts/SF-Pro-Display-Regular.otf'
    text = text.replace('\\n', '\n')
    
    try:
        font = ImageFont.truetype(font_path, font_size)
    except IOError:
        print("Font file not found. Please check the font path.")
        return
    
    # Calculate the size of the text
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Calculate the position for the text
    text_x = (result.width - text_width) // 2
    text_y = 265 - text_height/2  # Offset from top
    #fill=(190, 226, 255
    # Draw the text on the image
    draw.text((text_x, text_y), text, font=font, fill=(241,242,247), align='center')
    
    result.save(output_path)
    print(f"Output saved to {output_path}")


if __name__ == '__main__':
    args = parse_args()
    replace_dominant_color(args.template_path, args.source_path, args.output_path, args.text)


