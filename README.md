# MEX - Metadata Extractor

🔍 **Professional OSINT and Digital Forensics Metadata Analysis Tool**

MEX is a comprehensive, open-source metadata extraction and correlation utility designed for OSINT researchers, digital forensics investigators, and security professionals. It analyzes multiple file types, extracts metadata, identifies relationships across files, detects anomalies, and generates interactive reports.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![Status](https://img.shields.io/badge/status-stable-green.svg)

---

## ✨ Features

### 🎯 Core Capabilities

- **Multi-Format Support**: Extracts metadata from images, documents, videos, audio, archives, executables, and web files
- **Cross-File Correlation**: Identifies relationships between files based on shared metadata
- **Anomaly Detection**: Flags suspicious patterns and inconsistencies in metadata
- **Interactive Visualizations**: GPS maps, timelines, and relationship network graphs
- **Multiple Export Formats**: JSON, Markdown, TXT, and interactive HTML dashboards
- **CLI & GUI**: Both command-line interface and Streamlit web interface

### 📂 Supported File Types

| Category | Formats | Extracted Metadata |
|----------|---------|-------------------|
| **Images** | JPG, PNG, TIFF, HEIC, WebP | EXIF data, GPS coordinates, camera info, timestamps, software |
| **Documents** | PDF, DOCX, ODT, RTF | Author, title, company, creation dates, software |
| **Video/Audio** | MP4, MOV, MP3, WAV, AVI | Codec, duration, device info, GPS, artist, tags |
| **Archives** | ZIP, RAR, 7Z, TAR | File lists, timestamps, compression info, recursive analysis |
| **Executables** | EXE, DLL, ELF, Mach-O | Compilation date, compiler, imports, digital signature |
| **Web** | HTML, HTM, XML | Meta tags, OpenGraph, author, generator, embedded links |

### 🔗 Correlation Analysis

MEX automatically identifies relationships between files:

- **Shared Authors**: Files created by the same person
- **Same Device**: Files from identical cameras or devices
- **GPS Proximity**: Files taken at similar locations
- **Timestamp Clustering**: Files created within similar timeframes
- **Common Software**: Files edited with the same applications
- **Duplicate Detection**: Identifies identical files via hash comparison

### ⚠️ Anomaly Detection

Automatically flags suspicious metadata patterns:

- Modified date earlier than creation date
- Software version inconsistencies
- GPS coordinates inconsistent with timestamps
- Future timestamps
- Stripped or missing metadata
- Impossible software/date combinations

---

## 🚀 Installation

### Prerequisites

- Python 3.10 or higher
- pip package manager

### Install Dependencies

```bash
# Clone the repository
git clone https://github.com/yourusername/MEX.git
cd MEX

# Install required packages
pip install -r requirements.txt
```

### Dependencies

MEX uses the following libraries:

- **Metadata Extraction**: exifread, Pillow, pdfminer.six, python-docx, mutagen, hachoir, pefile, lief, beautifulsoup4
- **Analysis**: networkx, python-dateutil
- **Visualization**: folium, plotly, pyvis
- **GUI**: streamlit
- **Utilities**: tqdm, olefile, py7zr, rarfile

---

## 📖 Usage

### Command-Line Interface (CLI)

#### Basic Usage

```bash
# Analyze a single file
python main.py --input photo.jpg --export json

# Analyze a directory (non-recursive)
python main.py --input ./evidence --export html json txt

# Recursive directory analysis with full correlation
python main.py --input ./evidence --recursive --analyze --export html

# Compare two files
python main.py --compare file1.jpg file2.jpg --export markdown
```

#### CLI Options

| Option | Description |
|--------|-------------|
| `--input <path>` | Input file or directory path |
| `--analyze` | Enable correlation and anomaly detection |
| `--compare <file1> <file2>` | Compare metadata between two files |
| `--export <formats>` | Export formats: html, json, txt, markdown (default: json) |
| `--output <dir>` | Output directory (default: ./reports) |
| `--recursive` | Recursive directory scanning |
| `--version` | Show version information |

#### Examples

```bash
# Full forensic analysis with all export formats
python main.py --input ./case_files --recursive --analyze \
  --export html json txt markdown --output ./investigation_report

# Quick metadata extraction
python main.py --input suspicious_photo.jpg --export json

# Compare two versions of a document
python main.py --compare original.pdf modified.pdf --export markdown
```

### Streamlit GUI

Launch the interactive web interface:

```bash
streamlit run gui.py
```

The GUI provides:

- 📄 **Single File Analysis**: Upload and analyze individual files
- 📁 **Multiple Files**: Batch processing with correlation
- ⚖️ **Compare Mode**: Side-by-side file comparison
- 📊 **Interactive Visualizations**: Real-time charts and graphs
- 💾 **Easy Export**: Download reports in multiple formats

---

## 📊 Output Formats

### JSON Export

Structured data format ideal for automation and integration:

```json
{
  "metadata": {
    "export_date": "2024-01-15T10:30:00",
    "total_files": 25,
    "mex_version": "1.0.0"
  },
  "files": [...],
  "correlation": {...},
  "anomalies": {...}
}
```

### HTML Dashboard

Interactive report with:

- 📍 **GPS Map**: Folium-powered location visualization
- 🕒 **Timeline**: Plotly timeline of file creation/modification
- 🔗 **Relationship Graph**: PyVis network diagram
- 📊 **Statistics**: File type distribution and anomaly charts
- ⚠️ **Anomaly Report**: Color-coded severity indicators

### Markdown/Text Reports

Human-readable summary reports perfect for documentation and reporting.

---

## 🏗️ Project Structure

```
MEX/
├── mex/                          # Core package
│   ├── core/                     # Metadata extractors
│   │   ├── extractor_images.py
│   │   ├── extractor_documents.py
│   │   ├── extractor_videos.py
│   │   ├── extractor_archives.py
│   │   ├── extractor_executables.py
│   │   └── extractor_web.py
│   ├── correlate.py             # Correlation engine
│   ├── analyze.py               # Anomaly detection
│   ├── visualize.py             # Visualization module
│   ├── export.py                # Export handlers
│   └── utils.py                 # Utility functions
├── examples/                     # Sample files
│   └── sample_files/
├── main.py                       # CLI interface
├── gui.py                        # Streamlit GUI
├── requirements.txt              # Dependencies
└── README.md                     # Documentation
```

---

## 🧪 Testing

MEX includes a comprehensive test suite with sample files:

```bash
# Create sample test files
python examples/create_sample_files.py

# Run analysis on test files
python main.py --input examples/sample_files --analyze --export html

# Test GUI with samples
streamlit run gui.py
# Then upload files from examples/sample_files/
```

Test files include:
- Images with/without EXIF data
- Documents with metadata
- HTML files with meta tags
- Archives with nested files
- Files with anomalous timestamps

---

## 🔬 Use Cases

### OSINT Investigations

- **Social Media Analysis**: Extract location and device data from posted images
- **Document Attribution**: Identify authors and creation software
- **Timeline Reconstruction**: Build event timelines from file metadata

### Digital Forensics

- **Evidence Correlation**: Link files across different sources
- **Tampering Detection**: Identify modified or suspicious files
- **Chain of Custody**: Document file origins and modifications

### Security Research

- **Malware Analysis**: Examine executable metadata and compilation dates
- **Data Leakage**: Detect unintended metadata in published files
- **Website Fingerprinting**: Analyze web page metadata and technologies

---

## 🛠️ Advanced Features

### Recursive Archive Analysis

MEX automatically extracts and analyzes files within archives:

```bash
python main.py --input evidence.zip --analyze --export html
```

This will:
1. Extract the archive
2. Analyze each contained file
3. Correlate metadata across archive contents
4. Include results in the final report

### GPS Visualization

Files with GPS data are automatically plotted on an interactive map:

- Marker clustering for dense data
- Popup information with timestamps
- Export as standalone HTML

### Relationship Graphs

Network visualization shows connections:

- Node size based on connection count
- Edge colors indicate relationship types
- Interactive exploration with zoom/pan

---

## 📝 API Usage

Use MEX modules in your own Python scripts:

```python
from mex.core import ImageExtractor
from mex.correlate import MetadataCorrelator
from mex.analyze import AnomalyDetector

# Extract metadata
metadata = ImageExtractor.extract('photo.jpg')

# Correlate multiple files
metadata_list = [...]
correlator = MetadataCorrelator(metadata_list)
results = correlator.correlate()

# Detect anomalies
detector = AnomalyDetector(metadata_list)
anomalies = detector.analyze()
```

---

## 🤝 Contributing

Contributions are welcome! Here's how to help:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/NewExtractor`
3. **Make your changes**
4. **Test thoroughly**
5. **Submit a pull request**

### Adding New File Type Support

To add support for a new file type:

1. Create a new extractor in `mex/core/`
2. Implement the `can_extract()` and `extract()` methods
3. Return metadata using the standard template
4. Update `mex/core/__init__.py` to include the new extractor
5. Add test files to `examples/sample_files/`

---

## 📄 License

MEX is released under the MIT License. See [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

MEX builds upon excellent open-source libraries:

- **exifread** & **Pillow** for image metadata
- **pdfminer.six** & **python-docx** for document analysis
- **hachoir** & **mutagen** for media files
- **pefile** & **lief** for executable analysis
- **networkx**, **folium**, **plotly** for visualizations

---

## 🔮 Roadmap

Planned features for future versions:

- [ ] Real-time web scraping and metadata extraction
- [ ] Machine learning-based anomaly scoring
- [ ] Integration with external OSINT APIs
- [ ] PDF report generation with charts
- [ ] Docker containerization
- [ ] REST API for remote analysis
- [ ] Batch processing improvements
- [ ] Additional file format support

---

## ⚖️ Disclaimer

MEX is designed for legitimate OSINT research, digital forensics, and security analysis. Users are responsible for ensuring their use complies with applicable laws and regulations. I assume no liability for misuse of this tool.

---

**Built with ❤️ for the OSINT and InfoSec community**

*MEX v1.0.0*


