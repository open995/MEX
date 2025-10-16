# MEX Sample Test Files

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
