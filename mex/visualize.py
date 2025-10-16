"""
Visualization module for MEX.
Creates interactive maps, timelines, and relationship graphs.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class MetadataVisualizer:
    """Create visualizations from metadata and analysis results."""
    
    def __init__(self, metadata_list: List[Dict[str, Any]], 
                 correlation_data: Optional[Dict[str, Any]] = None,
                 anomaly_data: Optional[Dict[str, Any]] = None):
        """
        Initialize visualizer.
        
        Args:
            metadata_list: List of metadata dictionaries
            correlation_data: Correlation analysis results
            anomaly_data: Anomaly detection results
        """
        self.metadata_list = metadata_list
        self.correlation_data = correlation_data or {}
        self.anomaly_data = anomaly_data or {}
    
    def create_gps_map(self, output_path: str = None) -> Optional[str]:
        """
        Create interactive GPS map using folium.
        
        Args:
            output_path: Path to save HTML map
            
        Returns:
            HTML string or path to saved file
        """
        try:
            import folium
            from folium import plugins
            
            # Collect GPS data
            gps_points = []
            for metadata in self.metadata_list:
                file_name = metadata.get('file_info', {}).get('name')
                img_meta = metadata.get('metadata', {}).get('exif', {})
                gps = img_meta.get('gps', {}).get('coordinates')
                
                if gps and 'latitude' in gps and 'longitude' in gps:
                    gps_points.append({
                        'file': file_name,
                        'lat': gps['latitude'],
                        'lon': gps['longitude'],
                        'timestamp': img_meta.get('dates', {}).get('datetime_original', 'Unknown')
                    })
            
            if not gps_points:
                logger.warning("No GPS data found for map creation")
                return None
            
            # Calculate center point
            avg_lat = sum(p['lat'] for p in gps_points) / len(gps_points)
            avg_lon = sum(p['lon'] for p in gps_points) / len(gps_points)
            
            # Create map
            m = folium.Map(location=[avg_lat, avg_lon], zoom_start=12)
            
            # Add markers
            for point in gps_points:
                folium.Marker(
                    location=[point['lat'], point['lon']],
                    popup=f"<b>{point['file']}</b><br>{point['timestamp']}",
                    tooltip=point['file'],
                    icon=folium.Icon(color='red', icon='info-sign')
                ).add_to(m)
            
            # Add marker cluster
            marker_cluster = plugins.MarkerCluster().add_to(m)
            for point in gps_points:
                folium.Marker(
                    location=[point['lat'], point['lon']],
                    popup=point['file']
                ).add_to(marker_cluster)
            
            # Save or return HTML
            if output_path:
                m.save(output_path)
                return output_path
            else:
                return m._repr_html_()
                
        except Exception as e:
            logger.error(f"Error creating GPS map: {e}")
            return None
    
    def create_timeline(self, output_path: str = None) -> Optional[str]:
        """
        Create interactive timeline using plotly.
        
        Args:
            output_path: Path to save HTML timeline
            
        Returns:
            HTML string or path to saved file
        """
        try:
            import plotly.graph_objects as go
            import plotly.express as px
            from dateutil import parser as date_parser
            
            # Collect timeline data
            timeline_data = []
            for metadata in self.metadata_list:
                file_name = metadata.get('file_info', {}).get('name')
                file_type = metadata.get('file_info', {}).get('type')
                
                # Try to get creation date from various sources
                dates = []
                
                # File system dates
                ts = metadata.get('timestamps', {})
                if ts.get('created'):
                    dates.append(('Created', ts['created']))
                if ts.get('modified'):
                    dates.append(('Modified', ts['modified']))
                
                # EXIF dates
                exif_dates = metadata.get('metadata', {}).get('exif', {}).get('dates', {})
                if exif_dates.get('datetime_original'):
                    dates.append(('EXIF Original', exif_dates['datetime_original']))
                
                # Document dates
                doc = metadata.get('metadata', {}).get('document', {})
                if doc.get('created'):
                    dates.append(('Doc Created', doc['created']))
                
                for date_type, date_str in dates:
                    try:
                        dt = date_parser.parse(date_str)
                        timeline_data.append({
                            'file': file_name,
                            'date': dt,
                            'type': file_type,
                            'date_type': date_type
                        })
                    except:
                        pass
            
            if not timeline_data:
                logger.warning("No timeline data found")
                return None
            
            # Create timeline visualization
            fig = px.scatter(
                timeline_data,
                x='date',
                y='file',
                color='type',
                hover_data=['date_type'],
                title='File Timeline',
                labels={'date': 'Date/Time', 'file': 'File Name', 'type': 'File Type'}
            )
            
            fig.update_layout(
                height=max(400, len(set(d['file'] for d in timeline_data)) * 30),
                showlegend=True
            )
            
            # Save or return HTML
            if output_path:
                fig.write_html(output_path)
                return output_path
            else:
                return fig.to_html()
                
        except Exception as e:
            logger.error(f"Error creating timeline: {e}")
            return None
    
    def create_relationship_graph(self, output_path: str = None) -> Optional[str]:
        """
        Create interactive relationship network graph using PyVis.
        
        Args:
            output_path: Path to save HTML graph
            
        Returns:
            HTML string or path to saved file
        """
        try:
            from pyvis.network import Network
            
            if not self.correlation_data or not self.correlation_data.get('graph'):
                logger.warning("No correlation data available for graph")
                return None
            
            graph = self.correlation_data['graph']
            
            # Create PyVis network
            net = Network(height='600px', width='100%', 
                         bgcolor='#222222', font_color='white')
            
            # Add nodes
            for node in graph.nodes():
                net.add_node(node, label=node, title=node)
            
            # Add edges with relationship info
            for edge in graph.edges(data=True):
                source, target, data = edge
                relationship = data.get('relationship', 'related')
                
                # Color edges by relationship type
                color_map = {
                    'shared_author': '#ff6b6b',
                    'shared_device': '#4ecdc4',
                    'shared_location': '#45b7d1',
                    'similar_timestamp': '#f9ca24',
                    'shared_software': '#6c5ce7',
                    'duplicate': '#fd79a8'
                }
                color = color_map.get(relationship, '#95a5a6')
                
                net.add_edge(source, target, 
                           title=relationship,
                           color=color)
            
            # Configure physics
            net.set_options("""
            {
              "physics": {
                "forceAtlas2Based": {
                  "gravitationalConstant": -50,
                  "centralGravity": 0.01,
                  "springLength": 100,
                  "springConstant": 0.08
                },
                "maxVelocity": 50,
                "solver": "forceAtlas2Based",
                "timestep": 0.35,
                "stabilization": {"iterations": 150}
              }
            }
            """)
            
            # Save or return HTML
            if output_path:
                net.save_graph(output_path)
                return output_path
            else:
                return net.generate_html()
                
        except Exception as e:
            logger.error(f"Error creating relationship graph: {e}")
            return None
    
    def create_statistics_charts(self) -> Dict[str, Any]:
        """
        Create summary statistics charts.
        
        Returns:
            Dictionary with chart data
        """
        try:
            import plotly.graph_objects as go
            
            charts = {}
            
            # File type distribution
            type_counts = {}
            for metadata in self.metadata_list:
                file_type = metadata.get('file_info', {}).get('type', 'unknown')
                type_counts[file_type] = type_counts.get(file_type, 0) + 1
            
            fig_types = go.Figure(data=[go.Pie(
                labels=list(type_counts.keys()),
                values=list(type_counts.values()),
                hole=.3
            )])
            fig_types.update_layout(title_text='File Type Distribution')
            charts['file_types'] = fig_types.to_html(include_plotlyjs=False)
            
            # Anomaly distribution
            if self.anomaly_data and self.anomaly_data.get('anomalies'):
                severity_counts = {'high': 0, 'medium': 0, 'low': 0}
                for anomaly in self.anomaly_data['anomalies']:
                    severity = anomaly.get('severity', 'low')
                    severity_counts[severity] += 1
                
                fig_anomalies = go.Figure(data=[go.Bar(
                    x=list(severity_counts.keys()),
                    y=list(severity_counts.values()),
                    marker_color=['red', 'orange', 'yellow']
                )])
                fig_anomalies.update_layout(title_text='Anomalies by Severity')
                charts['anomalies'] = fig_anomalies.to_html(include_plotlyjs=False)
            
            # Relationship distribution
            if self.correlation_data and self.correlation_data.get('relationships'):
                rel_types = {}
                for rel in self.correlation_data['relationships']:
                    rel_type = rel.get('type', 'unknown')
                    rel_types[rel_type] = rel_types.get(rel_type, 0) + 1
                
                fig_relationships = go.Figure(data=[go.Bar(
                    x=list(rel_types.keys()),
                    y=list(rel_types.values())
                )])
                fig_relationships.update_layout(
                    title_text='Relationship Types',
                    xaxis_tickangle=-45
                )
                charts['relationships'] = fig_relationships.to_html(include_plotlyjs=False)
            
            return charts
            
        except Exception as e:
            logger.error(f"Error creating statistics charts: {e}")
            return {}


