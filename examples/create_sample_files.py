#!/usr/bin/env python3
"""
Script to create sample test files for MEX.
"""

import os
from pathlib import Path
from PIL import Image, ImageDraw
from datetime import datetime
import zipfile
import json

# Create sample directory
sample_dir = Path(__file__).parent / 'sample_files'
sample_dir.mkdir(exist_ok=True)

print("Creating sample test files for MEX...\n")

# 1. Create sample images with EXIF data
print("1. Creating sample images...")

# Simple PNG
img_png = Image.new('RGB', (100, 100), color='blue')
draw = ImageDraw.Draw(img_png)
draw.text((10, 40), "MEX Test", fill='white')
img_png.save(sample_dir / 'test_image.png')
print("   [+] test_image.png created")

# JPG with basic metadata (Note: PIL has limited EXIF writing capabilities)
img_jpg = Image.new('RGB', (200, 150), color='red')
draw = ImageDraw.Draw(img_jpg)
draw.text((50, 60), "Sample JPG", fill='white')
img_jpg.save(sample_dir / 'test_photo.jpg', quality=95)
print("   [+] test_photo.jpg created")

# 2. Create sample documents
print("\n2. Creating sample documents...")

# Create a simple text file (can be read as document)
with open(sample_dir / 'test_document.txt', 'w') as f:
    f.write("MEX Test Document\n")
    f.write("=" * 50 + "\n\n")
    f.write("This is a sample text file for testing MEX metadata extraction.\n")
    f.write(f"Created: {datetime.now().isoformat()}\n")
print("   [+] test_document.txt created")

# 3. Create sample HTML file
print("\n3. Creating sample HTML file...")

html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="author" content="MEX Test Suite">
    <meta name="description" content="Sample HTML file for metadata extraction testing">
    <meta name="keywords" content="MEX, metadata, testing, OSINT">
    <meta name="generator" content="MEX Test Generator v1.0">
    <meta property="og:title" content="MEX Test Page">
    <meta property="og:description" content="OpenGraph test data">
    <title>MEX Test HTML</title>
</head>
<body>
    <h1>MEX Test HTML File</h1>
    <p>This HTML file contains various metadata for testing.</p>
    <!-- Comment with email: test@mex-extractor.local -->
</body>
</html>
"""

with open(sample_dir / 'test_webpage.html', 'w') as f:
    f.write(html_content)
print("   [+] test_webpage.html created")

# 4. Create sample archive with files
print("\n4. Creating sample archive...")

with zipfile.ZipFile(sample_dir / 'test_archive.zip', 'w') as zf:
    # Add the text file
    zf.write(sample_dir / 'test_document.txt', 'document.txt')
    # Add the HTML file
    zf.write(sample_dir / 'test_webpage.html', 'webpage.html')
    # Add a JSON file
    test_json = {'test': 'data', 'timestamp': datetime.now().isoformat()}
    zf.writestr('data.json', json.dumps(test_json, indent=2))
print("   [+] test_archive.zip created (contains 3 files)")

# 5. Create sample JSON file
print("\n5. Creating sample JSON metadata file...")

metadata_sample = {
    'format': 'MEX Test Data',
    'version': '1.0',
    'created': datetime.now().isoformat(),
    'author': 'MEX Test Suite',
    'data': {
        'key1': 'value1',
        'key2': 'value2',
        'nested': {
            'item': 'test'
        }
    }
}

with open(sample_dir / 'test_metadata.json', 'w') as f:
    json.dump(metadata_sample, f, indent=2)
print("   [+] test_metadata.json created")

# 6. Create anomaly test files
print("\n6. Creating anomaly test files...")

# File with future timestamp (simulate by creating then modifying metadata if possible)
with open(sample_dir / 'suspicious_dates.txt', 'w') as f:
    f.write("This file is for testing timestamp anomaly detection.\n")
    f.write("The file system might show unusual date patterns.\n")
print("   [+] suspicious_dates.txt created")

# File with minimal metadata (stripped)
img_stripped = Image.new('RGB', (50, 50), color='green')
img_stripped.save(sample_dir / 'stripped_metadata.png')
print("   [+] stripped_metadata.png created (minimal metadata)")

# 7. Create README for samples
print("\n7. Creating sample files README...")

readme_content = """# MEX Sample Test Files

This directory contains sample files for testing MEX functionality.

## Files Included:

### Images
- `test_image.png` - Simple PNG image
- `test_photo.jpg` - Sample JPEG image
- `stripped_metadata.png` - Image with minimal metadata (for anomaly testing)

### Documents
- `test_document.txt` - Plain text document
- `test_metadata.json` - JSON metadata file

### Web
- `test_webpage.html` - HTML file with meta tags and OpenGraph data

### Archives
- `test_archive.zip` - ZIP archive containing multiple files

### Anomaly Testing
- `suspicious_dates.txt` - For timestamp anomaly detection

## Usage

Run MEX on these files to test all extractors:

```bash
# Analyze single file
python main.py --input examples/sample_files/test_photo.jpg --export html json

# Analyze all samples
python main.py --input examples/sample_files --recursive --analyze --export html

# Compare two files
python main.py --compare examples/sample_files/test_image.png examples/sample_files/test_photo.jpg --export markdown
```

## GUI Testing

```bash
streamlit run gui.py
```

Then upload these sample files through the web interface.
"""

with open(sample_dir / 'README.md', 'w') as f:
    f.write(readme_content)
print("   [+] README.md created")

print(f"\n[SUCCESS] Sample test suite created successfully in: {sample_dir}")
print(f"   Total files: {len(list(sample_dir.glob('*')))}")
print("\nYou can now test MEX with these sample files:")
print(f"   python main.py --input {sample_dir} --analyze --export html json txt")

