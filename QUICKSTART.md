# MEX Quick Start Guide

Get up and running with MEX in 5 minutes!

## 🚀 Quick Installation

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Create sample test files
python examples/create_sample_files.py

# 3. Run your first analysis
python main.py --input examples/sample_files --analyze --export html
```

## 📋 Common Commands

### Analyze a Single File
```bash
python main.py --input photo.jpg --export json
```

### Analyze a Directory
```bash
python main.py --input ./photos --recursive --analyze --export html json
```

### Compare Two Files
```bash
python main.py --compare file1.jpg file2.jpg --export markdown
```

### Launch GUI
```bash
streamlit run gui.py
```

## 📊 Understanding Output

After running analysis, check the `reports/` folder for:

- **report.json** - Structured data (for scripting)
- **report.html** - Interactive dashboard (open in browser)
- **report.txt** - Plain text summary
- **map.html** - GPS visualization (if GPS data found)
- **graph.html** - Relationship network

## 💡 Tips

1. **Use `--analyze` flag** for correlation and anomaly detection
2. **Recursive mode** scans subdirectories: `--recursive`
3. **Multiple exports** possible: `--export html json txt markdown`
4. **GUI is easier** for beginners: `streamlit run gui.py`

## 🎯 Example Workflow

```bash
# Step 1: Analyze evidence folder
python main.py --input ./evidence --recursive --analyze \
  --export html json --output ./case_001

# Step 2: Open the HTML dashboard
# Navigate to: case_001/report.html in your browser

# Step 3: Review findings
# - Check anomalies section for suspicious files
# - Examine relationship graph for connections
# - View GPS map if location data exists
```

## ⚠️ Troubleshooting

**Error: Module not found**
```bash
pip install -r requirements.txt
```

**Error: No files found**
```bash
# Check path is correct
python main.py --input "C:/full/path/to/files" --analyze
```

**GUI won't start**
```bash
# Install streamlit
pip install streamlit

# Run with full path
streamlit run gui.py
```

## 📚 Next Steps

- Read [README.md](README.md) for complete documentation
- Explore `examples/sample_files/` for test data
- Check [Use Cases](README.md#-use-cases) for ideas
- Review [API Usage](README.md#-api-usage) for scripting

Happy analyzing! 🔍

