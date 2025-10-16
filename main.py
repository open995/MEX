#!/usr/bin/env python3
"""
MEX - Metadata Extractor CLI Interface
Professional OSINT and digital forensics metadata analysis tool.
"""

import argparse
import sys
import os
from pathlib import Path
from typing import List, Dict, Any
from tqdm import tqdm

from mex.core import (
    ImageExtractor, DocumentExtractor, VideoExtractor,
    ArchiveExtractor, ExecutableExtractor, WebExtractor
)
from mex.correlate import MetadataCorrelator
from mex.analyze import AnomalyDetector
from mex.visualize import MetadataVisualizer
from mex.export import MetadataExporter
from mex.utils import get_file_type, validate_file_path


def extract_metadata(file_path: str) -> Dict[str, Any]:
    """Extract metadata from a single file."""
    extractors = [
        ImageExtractor,
        DocumentExtractor,
        VideoExtractor,
        ArchiveExtractor,
        ExecutableExtractor,
        WebExtractor
    ]
    
    for extractor in extractors:
        if extractor.can_extract(file_path):
            return extractor.extract(file_path)
    
    # If no specific extractor, return basic file info
    from mex.utils import create_metadata_template, compute_file_hash, format_timestamp
    metadata = create_metadata_template()
    path = Path(file_path)
    stat = path.stat()
    
    metadata['file_info'].update({
        'name': path.name,
        'path': str(path.absolute()),
        'size': stat.st_size,
        'type': get_file_type(file_path)['category'],
        'hash_md5': compute_file_hash(file_path, 'md5'),
        'hash_sha256': compute_file_hash(file_path, 'sha256')
    })
    
    metadata['timestamps'].update({
        'created': format_timestamp(stat.st_ctime),
        'modified': format_timestamp(stat.st_mtime),
        'accessed': format_timestamp(stat.st_atime)
    })
    
    return metadata


def collect_files(input_path: str, recursive: bool = False) -> List[str]:
    """Collect all files from input path."""
    files = []
    path = Path(input_path)
    
    if path.is_file():
        files.append(str(path))
    elif path.is_dir():
        if recursive:
            for root, _, filenames in os.walk(path):
                for filename in filenames:
                    files.append(os.path.join(root, filename))
        else:
            files = [str(f) for f in path.iterdir() if f.is_file()]
    
    return files


def compare_files(file1: str, file2: str) -> Dict[str, Any]:
    """Compare metadata between two files."""
    meta1 = extract_metadata(file1)
    meta2 = extract_metadata(file2)
    
    comparison = {
        'file1': meta1,
        'file2': meta2,
        'differences': [],
        'similarities': []
    }
    
    # Compare hashes
    hash1 = meta1.get('file_info', {}).get('hash_sha256')
    hash2 = meta2.get('file_info', {}).get('hash_sha256')
    
    if hash1 == hash2:
        comparison['similarities'].append('Files are identical (same hash)')
    else:
        comparison['differences'].append('Files have different content (different hash)')
    
    # Compare timestamps
    ts1 = meta1.get('timestamps', {})
    ts2 = meta2.get('timestamps', {})
    
    if ts1.get('created') == ts2.get('created'):
        comparison['similarities'].append('Same creation date')
    else:
        comparison['differences'].append(f"Different creation dates: {ts1.get('created')} vs {ts2.get('created')}")
    
    # Compare metadata
    # (Add more detailed comparison logic as needed)
    
    return comparison


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='MEX - Metadata Extractor for OSINT and Digital Forensics',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s --input ./evidence --analyze --export html json txt --output ./reports
  %(prog)s --compare file1.jpg file2.jpg --export markdown
  %(prog)s --input ./media --analyze --export html
        '''
    )
    
    parser.add_argument('--input', type=str, help='Input file or directory path')
    parser.add_argument('--analyze', action='store_true', help='Enable full analysis and correlation')
    parser.add_argument('--compare', nargs=2, metavar=('FILE1', 'FILE2'), help='Compare metadata between two files')
    parser.add_argument('--export', nargs='+', choices=['html', 'json', 'txt', 'markdown'], 
                       default=['json'], help='Export formats (default: json)')
    parser.add_argument('--output', type=str, default='./reports', help='Output directory (default: ./reports)')
    parser.add_argument('--recursive', action='store_true', help='Recursive directory scanning')
    parser.add_argument('--version', action='version', version='%(prog)s 1.0.0')
    
    args = parser.parse_args()
    
    # Validation
    if not args.input and not args.compare:
        parser.error('Either --input or --compare must be specified')
    
    print("🔍 MEX - Metadata Extractor v1.0.0")
    print("="*50)
    
    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Compare mode
    if args.compare:
        print(f"\nComparing files:")
        print(f"  File 1: {args.compare[0]}")
        print(f"  File 2: {args.compare[1]}")
        
        comparison = compare_files(args.compare[0], args.compare[1])
        
        # Export comparison
        if 'json' in args.export:
            import json
            output_path = output_dir / 'comparison.json'
            with open(output_path, 'w') as f:
                json.dump(comparison, f, indent=2, default=str)
            print(f"\n✓ JSON comparison saved to {output_path}")
        
        if 'markdown' in args.export or 'txt' in args.export:
            output_path = output_dir / 'comparison.md'
            with open(output_path, 'w') as f:
                f.write("# File Comparison Report\n\n")
                f.write(f"## File 1: {args.compare[0]}\n\n")
                f.write(f"## File 2: {args.compare[1]}\n\n")
                f.write("### Similarities\n\n")
                for sim in comparison['similarities']:
                    f.write(f"- {sim}\n")
                f.write("\n### Differences\n\n")
                for diff in comparison['differences']:
                    f.write(f"- {diff}\n")
            print(f"✓ Comparison report saved to {output_path}")
        
        return 0
    
    # Analysis mode
    print(f"\n📂 Collecting files from: {args.input}")
    files = collect_files(args.input, args.recursive)
    print(f"   Found {len(files)} file(s)")
    
    # Extract metadata
    print("\n📊 Extracting metadata...")
    metadata_list = []
    for file_path in tqdm(files, desc="Processing"):
        try:
            metadata = extract_metadata(file_path)
            metadata_list.append(metadata)
        except Exception as e:
            print(f"   ⚠️  Error processing {file_path}: {e}")
    
    print(f"   Successfully processed {len(metadata_list)} file(s)")
    
    # Analysis and correlation
    correlation_data = None
    anomaly_data = None
    visualizations = {}
    
    if args.analyze:
        print("\n🔗 Running correlation analysis...")
        correlator = MetadataCorrelator(metadata_list)
        correlation_data = correlator.correlate()
        print(f"   Found {correlation_data.get('total_relationships', 0)} relationship(s)")
        
        print("\n⚠️  Running anomaly detection...")
        detector = AnomalyDetector(metadata_list)
        anomaly_data = detector.analyze()
        print(f"   Detected {anomaly_data.get('total_anomalies', 0)} anomalie(s)")
        
        print("\n📈 Creating visualizations...")
        visualizer = MetadataVisualizer(metadata_list, correlation_data, anomaly_data)
        
        # Create visualizations and save separately
        map_path = visualizer.create_gps_map(str(output_dir / 'map.html'))
        if map_path:
            visualizations['map'] = 'map.html'
            print(f"   ✓ GPS map saved")
        
        timeline_html = visualizer.create_timeline()
        if timeline_html:
            visualizations['timeline'] = timeline_html
            print(f"   ✓ Timeline created")
        
        graph_path = visualizer.create_relationship_graph(str(output_dir / 'graph.html'))
        if graph_path:
            visualizations['graph'] = 'graph.html'
            print(f"   ✓ Relationship graph saved")
    
    # Export results
    print(f"\n💾 Exporting results...")
    exporter = MetadataExporter(metadata_list, correlation_data, anomaly_data, visualizations)
    
    for export_format in args.export:
        if export_format == 'json':
            output_path = output_dir / 'report.json'
            if exporter.export_json(str(output_path)):
                print(f"   ✓ JSON report: {output_path}")
        
        elif export_format == 'markdown':
            output_path = output_dir / 'report.md'
            if exporter.export_markdown(str(output_path)):
                print(f"   ✓ Markdown report: {output_path}")
        
        elif export_format == 'txt':
            output_path = output_dir / 'report.txt'
            if exporter.export_txt(str(output_path)):
                print(f"   ✓ Text report: {output_path}")
        
        elif export_format == 'html':
            output_path = output_dir / 'report.html'
            if exporter.export_html(str(output_path)):
                print(f"   ✓ HTML dashboard: {output_path}")
    
    print(f"\n✅ Analysis complete! Results saved to {output_dir}")
    return 0


if __name__ == '__main__':
    sys.exit(main())

