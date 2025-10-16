"""
Export module for MEX.
Handles exporting analysis results in various formats.
"""

import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class MetadataExporter:
    """Export metadata and analysis results in various formats."""
    
    def __init__(self, metadata_list: List[Dict[str, Any]],
                 correlation_data: Optional[Dict[str, Any]] = None,
                 anomaly_data: Optional[Dict[str, Any]] = None,
                 visualizations: Optional[Dict[str, str]] = None):
        """
        Initialize exporter.
        
        Args:
            metadata_list: List of metadata dictionaries
            correlation_data: Correlation analysis results
            anomaly_data: Anomaly detection results
            visualizations: Dictionary of visualization HTML strings
        """
        self.metadata_list = metadata_list
        self.correlation_data = correlation_data or {}
        self.anomaly_data = anomaly_data or {}
        self.visualizations = visualizations or {}
    
    def export_json(self, output_path: str) -> bool:
        """
        Export all data as JSON.
        
        Args:
            output_path: Path to save JSON file
            
        Returns:
            True if successful
        """
        try:
            data = {
                'metadata': {
                    'export_date': datetime.now().isoformat(),
                    'total_files': len(self.metadata_list),
                    'mex_version': '1.0.0'
                },
                'files': self.metadata_list,
                'correlation': self.correlation_data,
                'anomalies': self.anomaly_data
            }
            
            # Convert NetworkX graph to serializable format
            if 'graph' in data['correlation']:
                import networkx as nx
                graph = data['correlation']['graph']
                data['correlation']['graph'] = {
                    'nodes': list(graph.nodes(data=True)),
                    'edges': list(graph.edges(data=True))
                }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
            
            logger.info(f"JSON export saved to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting JSON: {e}")
            return False
    
    def export_markdown(self, output_path: str) -> bool:
        """
        Export as Markdown report.
        
        Args:
            output_path: Path to save Markdown file
            
        Returns:
            True if successful
        """
        try:
            md = []
            md.append("# MEX Metadata Analysis Report\n")
            md.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
            
            # Summary
            md.append("## Summary\n")
            md.append(f"- **Total Files Analyzed:** {len(self.metadata_list)}\n")
            
            if self.correlation_data:
                md.append(f"- **Relationships Found:** {self.correlation_data.get('total_relationships', 0)}\n")
            
            if self.anomaly_data:
                md.append(f"- **Anomalies Detected:** {self.anomaly_data.get('total_anomalies', 0)}\n")
            
            md.append("\n---\n\n")
            
            # File Details
            md.append("## File Analysis\n\n")
            for idx, metadata in enumerate(self.metadata_list, 1):
                file_info = metadata.get('file_info', {})
                md.append(f"### {idx}. {file_info.get('name', 'Unknown')}\n\n")
                md.append(f"- **Type:** {file_info.get('type', 'unknown')}\n")
                md.append(f"- **Size:** {file_info.get('size', 0):,} bytes\n")
                md.append(f"- **SHA256:** `{file_info.get('hash_sha256', 'N/A')}`\n")
                
                # Timestamps
                timestamps = metadata.get('timestamps', {})
                if timestamps:
                    md.append(f"- **Created:** {timestamps.get('created', 'N/A')}\n")
                    md.append(f"- **Modified:** {timestamps.get('modified', 'N/A')}\n")
                
                md.append("\n")
            
            # Relationships
            if self.correlation_data and self.correlation_data.get('relationships'):
                md.append("## Relationships\n\n")
                for rel in self.correlation_data['relationships']:
                    md.append(f"### {rel['type'].replace('_', ' ').title()}\n\n")
                    md.append(f"- **Files:** {', '.join(rel['files'])}\n")
                    if 'value' in rel:
                        md.append(f"- **Value:** {rel['value']}\n")
                    md.append(f"- **Strength:** {rel['strength']}\n\n")
            
            # Anomalies
            if self.anomaly_data and self.anomaly_data.get('anomalies'):
                md.append("## Anomalies\n\n")
                
                # Group by severity
                by_severity = {'high': [], 'medium': [], 'low': []}
                for anomaly in self.anomaly_data['anomalies']:
                    severity = anomaly.get('severity', 'low')
                    by_severity[severity].append(anomaly)
                
                for severity in ['high', 'medium', 'low']:
                    if by_severity[severity]:
                        md.append(f"### {severity.upper()} Severity\n\n")
                        for anomaly in by_severity[severity]:
                            md.append(f"- **{anomaly['file']}:** {anomaly['description']}\n")
                        md.append("\n")
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(''.join(md))
            
            logger.info(f"Markdown export saved to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting Markdown: {e}")
            return False
    
    def export_txt(self, output_path: str) -> bool:
        """
        Export as plain text report.
        
        Args:
            output_path: Path to save text file
            
        Returns:
            True if successful
        """
        try:
            txt = []
            txt.append("="*70 + "\n")
            txt.append("MEX METADATA ANALYSIS REPORT\n")
            txt.append("="*70 + "\n\n")
            txt.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Summary
            txt.append("-"*70 + "\n")
            txt.append("SUMMARY\n")
            txt.append("-"*70 + "\n")
            txt.append(f"Total Files Analyzed: {len(self.metadata_list)}\n")
            
            if self.correlation_data:
                txt.append(f"Relationships Found: {self.correlation_data.get('total_relationships', 0)}\n")
            
            if self.anomaly_data:
                txt.append(f"Anomalies Detected: {self.anomaly_data.get('total_anomalies', 0)}\n")
            
            txt.append("\n")
            
            # File Details
            txt.append("-"*70 + "\n")
            txt.append("FILE ANALYSIS\n")
            txt.append("-"*70 + "\n\n")
            
            for idx, metadata in enumerate(self.metadata_list, 1):
                file_info = metadata.get('file_info', {})
                txt.append(f"{idx}. {file_info.get('name', 'Unknown')}\n")
                txt.append(f"   Type: {file_info.get('type', 'unknown')}\n")
                txt.append(f"   Size: {file_info.get('size', 0):,} bytes\n")
                txt.append(f"   SHA256: {file_info.get('hash_sha256', 'N/A')}\n\n")
            
            # Anomalies
            if self.anomaly_data and self.anomaly_data.get('anomalies'):
                txt.append("-"*70 + "\n")
                txt.append("ANOMALIES DETECTED\n")
                txt.append("-"*70 + "\n\n")
                
                for anomaly in self.anomaly_data['anomalies']:
                    txt.append(f"[{anomaly['severity'].upper()}] {anomaly['file']}\n")
                    txt.append(f"  {anomaly['description']}\n\n")
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(''.join(txt))
            
            logger.info(f"Text export saved to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting text: {e}")
            return False
    
    def export_html(self, output_path: str) -> bool:
        """
        Export as interactive HTML dashboard.
        
        Args:
            output_path: Path to save HTML file
            
        Returns:
            True if successful
        """
        try:
            html = []
            html.append("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MEX Metadata Analysis Report</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #1a1a1a;
            color: #e0e0e0;
            padding: 20px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }
        .header h1 { color: white; margin-bottom: 10px; }
        .header p { color: rgba(255,255,255,0.9); }
        .section {
            background: #2d2d2d;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .section h2 {
            color: #667eea;
            margin-bottom: 15px;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .stat-card {
            background: #3d3d3d;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }
        .stat-value {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }
        .stat-label { color: #a0a0a0; margin-top: 5px; }
        .file-item {
            background: #3d3d3d;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 10px;
        }
        .file-name { color: #667eea; font-weight: bold; }
        .file-detail { color: #a0a0a0; font-size: 0.9em; margin-top: 5px; }
        .anomaly {
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 10px;
        }
        .anomaly.high { background: rgba(244, 67, 54, 0.2); border-left: 4px solid #f44336; }
        .anomaly.medium { background: rgba(255, 152, 0, 0.2); border-left: 4px solid #ff9800; }
        .anomaly.low { background: rgba(255, 235, 59, 0.2); border-left: 4px solid #ffeb3b; }
        .visualization {
            background: #2d2d2d;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        iframe {
            width: 100%;
            height: 600px;
            border: none;
            border-radius: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 MEX Metadata Analysis Report</h1>
            <p>Generated on """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</p>
        </div>
""")
            
            # Summary Statistics
            html.append("""
        <div class="section">
            <h2>Summary Statistics</h2>
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-value">""" + str(len(self.metadata_list)) + """</div>
                    <div class="stat-label">Files Analyzed</div>
                </div>
""")
            
            if self.correlation_data:
                html.append("""
                <div class="stat-card">
                    <div class="stat-value">""" + str(self.correlation_data.get('total_relationships', 0)) + """</div>
                    <div class="stat-label">Relationships Found</div>
                </div>
""")
            
            if self.anomaly_data:
                html.append("""
                <div class="stat-card">
                    <div class="stat-value">""" + str(self.anomaly_data.get('total_anomalies', 0)) + """</div>
                    <div class="stat-label">Anomalies Detected</div>
                </div>
""")
            
            html.append("""
            </div>
        </div>
""")
            
            # Visualizations
            if self.visualizations:
                if self.visualizations.get('map'):
                    html.append("""
        <div class="section">
            <h2>📍 GPS Location Map</h2>
            <iframe src=\"""" + self.visualizations['map'] + """\"></iframe>
        </div>
""")
                
                if self.visualizations.get('timeline'):
                    html.append("""
        <div class="section">
            <h2>🕒 Timeline</h2>
            <div class="visualization">
                """ + self.visualizations['timeline'] + """
            </div>
        </div>
""")
                
                if self.visualizations.get('graph'):
                    html.append("""
        <div class="section">
            <h2>🔗 Relationship Network</h2>
            <iframe src=\"""" + self.visualizations['graph'] + """\"></iframe>
        </div>
""")
            
            # File Details
            html.append("""
        <div class="section">
            <h2>File Details</h2>
""")
            
            for metadata in self.metadata_list[:20]:  # Limit to first 20
                file_info = metadata.get('file_info', {})
                html.append(f"""
            <div class="file-item">
                <div class="file-name">{file_info.get('name', 'Unknown')}</div>
                <div class="file-detail">Type: {file_info.get('type', 'unknown')} | Size: {file_info.get('size', 0):,} bytes</div>
                <div class="file-detail">SHA256: {file_info.get('hash_sha256', 'N/A')[:32]}...</div>
            </div>
""")
            
            html.append("""
        </div>
""")
            
            # Anomalies
            if self.anomaly_data and self.anomaly_data.get('anomalies'):
                html.append("""
        <div class="section">
            <h2>⚠️ Anomalies Detected</h2>
""")
                
                for anomaly in self.anomaly_data['anomalies']:
                    severity = anomaly.get('severity', 'low')
                    html.append(f"""
            <div class="anomaly {severity}">
                <strong>{anomaly['file']}</strong><br>
                {anomaly['description']}
            </div>
""")
                
                html.append("""
        </div>
""")
            
            html.append("""
    </div>
</body>
</html>
""")
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(''.join(html))
            
            logger.info(f"HTML export saved to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting HTML: {e}")
            return False


