import os
import argparse
from PIL import Image
import numpy as np
from sklearn.cluster import KMeans
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
import webcolors

def get_color_name(rgb):
    """
    Get the closest matching color name for an RGB value.
    """
    def rgb_to_name(rgb_tuple):
        # Dictionary of basic colors and their RGB values
        basic_colors = {
            'red': (255, 0, 0),
            'green': (0, 255, 0),
            'blue': (0, 0, 255),
            'yellow': (255, 255, 0),
            'orange': (255, 165, 0),
            'purple': (128, 0, 128),
            'brown': (165, 42, 42),
            'pink': (255, 192, 203),
            'grey': (128, 128, 128),
            'black': (0, 0, 0),
            'white': (255, 255, 255),
            'tan': (210, 180, 140),
            'light blue': (173, 216, 230),
            'dark blue': (0, 0, 139),
            'light green': (144, 238, 144),
            'dark green': (0, 100, 0),
            'light grey': (211, 211, 211),
            'dark grey': (169, 169, 169),
            'navy': (0, 0, 128),
            'maroon': (128, 0, 0)
        }
        
        min_distance = float('inf')
        closest_color = 'unknown'
        
        for color_name, color_rgb in basic_colors.items():
            distance = sum((c1 - c2) ** 2 for c1, c2 in zip(rgb_tuple, color_rgb))
            if distance < min_distance:
                min_distance = distance
                closest_color = color_name
                
        return closest_color
    
    return rgb_to_name(tuple(rgb))

def load_and_resize_image(image_path, target_width, target_height):
    """
    Load an image and resize it to the specified dimensions using nearest neighbor sampling
    to maintain sharp edges suitable for pixel art.
    """
    with Image.open(image_path) as img:
        if img.mode != 'RGB':
            img = img.convert('RGB')
        return img.resize((target_width, target_height), Image.Resampling.NEAREST)

def create_high_res_pixel_art(small_image, target_size=1000):
    """
    Scale up the pixel art to a higher resolution while maintaining sharp edges.
    Maintains aspect ratio while ensuring the longer side is target_size pixels.
    """
    width, height = small_image.size
    if width > height:
        new_width = target_size
        new_height = int(height * (target_size / width))
    else:
        new_height = target_size
        new_width = int(width * (target_size / height))
    
    return small_image.resize((new_width, new_height), Image.Resampling.NEAREST)

def quantize_colors(image, max_colors=8):
    """
    Reduce the number of colors in the image using K-means clustering.
    Returns the quantized image and the palette of colors used.
    """
    pixels = np.array(image)
    original_shape = pixels.shape
    pixels_2d = pixels.reshape(-1, 3)
    
    unique_colors = np.unique(pixels_2d, axis=0)
    n_colors = min(len(unique_colors), max_colors)
    
    kmeans = KMeans(n_clusters=n_colors, random_state=42)
    kmeans.fit(pixels_2d)
    
    palette = kmeans.cluster_centers_.astype(int)
    quantized_pixels = kmeans.predict(pixels_2d)
    
    color_mapping = {i: i+1 for i in range(n_colors)}
    color_grid = quantized_pixels.reshape(original_shape[:2])
    number_grid = np.vectorize(color_mapping.get)(color_grid)
    
    quantized_image = Image.fromarray(np.uint8(palette[quantized_pixels].reshape(original_shape)))
    
    return number_grid, palette, quantized_image

def create_numbered_pdf(number_grid, palette, output_path, title):
    """
    Create a PDF with the numbered grid and color key.
    Grid width is fixed at 8 inches on a standard 8.5x11" page.
    """
    c = canvas.Canvas(output_path, pagesize=letter)
    
    # Add title at the top
    c.setFont("Helvetica", 16)
    c.drawString(1 * inch, 10.5 * inch, title)
    
    # Set up dimensions
    grid_height, grid_width = number_grid.shape
    cell_size = 8 * inch / grid_width  # 8 inch width divided by number of cells
    
    # Calculate total grid height in inches
    grid_height_inches = cell_size * grid_height / inch
    
    # Start position (centering the grid horizontally)
    start_x = (8.5 * inch - (grid_width * cell_size)) / 2
    start_y = 10 * inch  # Start near top of page, leaving room for title
    
    # Draw grid and numbers
    for i in range(grid_height):
        for j in range(grid_width):
            # Draw cell borders
            x = start_x + (j * cell_size)
            y = start_y - ((i + 1) * cell_size)
            c.rect(x, y, cell_size, cell_size)
            
            # Add number (centered in cell)
            number = int(number_grid[i][j])
            c.setFont("Helvetica", min(cell_size * 0.7, 10))
            c.drawString(
                x + (cell_size * 0.4),
                y + (cell_size * 0.3),
                str(number)
            )
    
    # Add color key in multiple columns
    key_start_y = start_y - ((grid_height + 1) * cell_size)
    c.setFont("Helvetica", 12)
    c.drawString(start_x, key_start_y, "Color Key:")
    
    # Calculate column layout
    colors_per_column = 6
    column_width = 2 * inch
    num_columns = (len(palette) + colors_per_column - 1) // colors_per_column
    
    # Add color swatches and names in columns
    for i, color in enumerate(palette):
        column = i // colors_per_column
        row = i % colors_per_column
        
        x_pos = start_x + (column * column_width)
        y_pos = key_start_y - ((row + 1) * 20)
        
        # Draw number
        c.setFont("Helvetica", 12)
        c.drawString(x_pos, y_pos, f"{i + 1}:")
        
        # Draw color swatch
        c.setFillColorRGB(color[0]/255, color[1]/255, color[2]/255)
        c.rect(x_pos + 30, y_pos - 2, 15, 15, fill=1)
        
        # Draw color name
        c.setFillColorRGB(0, 0, 0)  # Reset to black
        color_name = get_color_name(color)
        c.drawString(x_pos + 60, y_pos, color_name)
    
    c.save()

def process_directory(width, height):
    """
    Process all images in the pics directory and create corresponding
    high-res pixel art images and PDF templates.
    """
    if not os.path.exists('pics'):
        raise Exception("Required 'pics' directory not found!")
    
    os.makedirs('pixel_art', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    
    print(f"Processing images to {width}x{height} pixel art...")
    
    for filename in os.listdir('pics'):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            base_name = os.path.splitext(filename)[0]
            image_path = os.path.join('pics', filename)
            
            print(f"Processing {filename}...")
            
            # Create low-res pixel art
            img = load_and_resize_image(image_path, width, height)
            
            # Quantize colors
            number_grid, palette, quantized_image = quantize_colors(img)
            
            # Create high-res version
            high_res_image = create_high_res_pixel_art(quantized_image)
            
            # Save high-res pixel art
            high_res_path = os.path.join('pixel_art', f"{base_name}_pixel_art.png")
            high_res_image.save(high_res_path)
            
            # Create PDF template with title
            pdf_path = os.path.join('templates', f"{base_name}_template.pdf")
            create_numbered_pdf(number_grid, palette, pdf_path, base_name)
            
            print(f"Created pixel art: {high_res_path}")
            print(f"Created template: {pdf_path}")

def main():
    """
    Main entry point of the program. Handles command line arguments
    and initiates the processing.
    """
    parser = argparse.ArgumentParser(
        description='Convert images to pixel art and create numbered templates'
    )
    parser.add_argument('width', type=int, help='Width of the pixel art grid')
    parser.add_argument('height', type=int, help='Height of the pixel art grid')
    
    args = parser.parse_args()
    
    if args.width < 1 or args.height < 1:
        raise ValueError("Width and height must be positive numbers")
    
    try:
        process_directory(args.width, args.height)
        print("Processing complete!")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()