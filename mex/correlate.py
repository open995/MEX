"""
Correlation engine for MEX.
Identifies relationships and connections between files based on metadata.
"""

import logging
from typing import List, Dict, Any, Set, Tuple
from collections import defaultdict
from datetime import datetime, timedelta
import networkx as nx
from dateutil import parser as date_parser

logger = logging.getLogger(__name__)


class MetadataCorrelator:
    """Correlate metadata across multiple files to find relationships."""
    
    def __init__(self, metadata_list: List[Dict[str, Any]]):
        """
        Initialize correlator with list of metadata dictionaries.
        
        Args:
            metadata_list: List of metadata dictionaries from extractors
        """
        self.metadata_list = metadata_list
        self.relationships = []
        self.graph = nx.Graph()
    
    def correlate(self) -> Dict[str, Any]:
        """
        Perform correlation analysis on all files.
        
        Returns:
            Dictionary containing correlation results and relationship graph
        """
        # Build graph with files as nodes
        for idx, metadata in enumerate(self.metadata_list):
            file_name = metadata.get('file_info', {}).get('name', f'file_{idx}')
            self.graph.add_node(file_name, **metadata)
        
        # Find relationships
        self._correlate_authors()
        self._correlate_devices()
        self._correlate_gps()
        self._correlate_timestamps()
        self._correlate_software()
        self._correlate_hashes()
        
        # Build relationship summary
        summary = self._build_summary()
        
        return {
            'total_files': len(self.metadata_list),
            'total_relationships': len(self.relationships),
            'relationships': self.relationships,
            'graph': self.graph,
            'summary': summary
        }
    
    def _correlate_authors(self):
        """Find files with shared authors."""
        author_map = defaultdict(list)
        
        for idx, metadata in enumerate(self.metadata_list):
            file_name = metadata.get('file_info', {}).get('name', f'file_{idx}')
            
            # Check various metadata locations for author
            authors = set()
            
            # Documents
            doc_meta = metadata.get('metadata', {}).get('document', {})
            if doc_meta.get('author'):
                authors.add(doc_meta['author'].lower().strip())
            
            # Images
            img_meta = metadata.get('metadata', {}).get('exif', {})
            if img_meta.get('software', {}).get('artist'):
                authors.add(img_meta['software']['artist'].lower().strip())
            
            # Media
            media_meta = metadata.get('metadata', {}).get('media', {}).get('audio_tags', {})
            if media_meta.get('artist'):
                authors.add(media_meta['artist'].lower().strip())
            
            for author in authors:
                author_map[author].append(file_name)
        
        # Create relationships
        for author, files in author_map.items():
            if len(files) > 1:
                self.relationships.append({
                    'type': 'shared_author',
                    'value': author,
                    'files': files,
                    'strength': 'high'
                })
                # Add edges to graph
                for i in range(len(files)):
                    for j in range(i + 1, len(files)):
                        self.graph.add_edge(files[i], files[j], 
                                          relationship='shared_author', 
                                          value=author)
    
    def _correlate_devices(self):
        """Find files created by the same device."""
        device_map = defaultdict(list)
        
        for idx, metadata in enumerate(self.metadata_list):
            file_name = metadata.get('file_info', {}).get('name', f'file_{idx}')
            
            # Check for device/camera information
            img_meta = metadata.get('metadata', {}).get('exif', {})
            camera = img_meta.get('camera', {})
            
            if camera.get('make') and camera.get('model'):
                device_id = f"{camera['make']} {camera['model']}".lower().strip()
                device_map[device_id].append(file_name)
        
        # Create relationships
        for device, files in device_map.items():
            if len(files) > 1:
                self.relationships.append({
                    'type': 'shared_device',
                    'value': device,
                    'files': files,
                    'strength': 'high'
                })
                # Add edges to graph
                for i in range(len(files)):
                    for j in range(i + 1, len(files)):
                        self.graph.add_edge(files[i], files[j],
                                          relationship='shared_device',
                                          value=device)
    
    def _correlate_gps(self, tolerance_km: float = 0.1):
        """
        Find files with similar GPS coordinates.
        
        Args:
            tolerance_km: Distance tolerance in kilometers
        """
        gps_data = []
        
        for idx, metadata in enumerate(self.metadata_list):
            file_name = metadata.get('file_info', {}).get('name', f'file_{idx}')
            
            # Check for GPS data
            img_meta = metadata.get('metadata', {}).get('exif', {})
            gps = img_meta.get('gps', {}).get('coordinates')
            
            if gps and 'latitude' in gps and 'longitude' in gps:
                gps_data.append({
                    'file': file_name,
                    'lat': gps['latitude'],
                    'lon': gps['longitude']
                })
        
        # Compare GPS coordinates
        for i in range(len(gps_data)):
            for j in range(i + 1, len(gps_data)):
                distance = self._calculate_distance(
                    gps_data[i]['lat'], gps_data[i]['lon'],
                    gps_data[j]['lat'], gps_data[j]['lon']
                )
                
                if distance <= tolerance_km:
                    self.relationships.append({
                        'type': 'shared_location',
                        'value': f"({gps_data[i]['lat']:.6f}, {gps_data[i]['lon']:.6f})",
                        'files': [gps_data[i]['file'], gps_data[j]['file']],
                        'distance_km': round(distance, 3),
                        'strength': 'high' if distance < 0.01 else 'medium'
                    })
                    self.graph.add_edge(gps_data[i]['file'], gps_data[j]['file'],
                                      relationship='shared_location',
                                      distance=distance)
    
    def _correlate_timestamps(self, tolerance_hours: int = 24):
        """
        Find files with timestamps in close proximity.
        
        Args:
            tolerance_hours: Time tolerance in hours
        """
        timestamp_data = []
        
        for idx, metadata in enumerate(self.metadata_list):
            file_name = metadata.get('file_info', {}).get('name', f'file_{idx}')
            
            # Collect various timestamps
            timestamps = []
            
            # File system timestamps
            ts = metadata.get('timestamps', {})
            if ts.get('created'):
                timestamps.append(ts['created'])
            
            # EXIF timestamps
            exif_dates = metadata.get('metadata', {}).get('exif', {}).get('dates', {})
            if exif_dates.get('datetime_original'):
                timestamps.append(exif_dates['datetime_original'])
            
            # Document timestamps
            doc = metadata.get('metadata', {}).get('document', {})
            if doc.get('created'):
                timestamps.append(doc['created'])
            
            for ts_str in timestamps:
                try:
                    dt = date_parser.parse(ts_str)
                    timestamp_data.append({
                        'file': file_name,
                        'datetime': dt,
                        'timestamp_str': ts_str
                    })
                except:
                    pass
        
        # Compare timestamps
        for i in range(len(timestamp_data)):
            for j in range(i + 1, len(timestamp_data)):
                if timestamp_data[i]['file'] == timestamp_data[j]['file']:
                    continue
                
                time_diff = abs((timestamp_data[i]['datetime'] - 
                               timestamp_data[j]['datetime']).total_seconds() / 3600)
                
                if time_diff <= tolerance_hours:
                    self.relationships.append({
                        'type': 'similar_timestamp',
                        'files': [timestamp_data[i]['file'], timestamp_data[j]['file']],
                        'time_diff_hours': round(time_diff, 2),
                        'strength': 'high' if time_diff < 1 else 'medium'
                    })
                    self.graph.add_edge(timestamp_data[i]['file'], 
                                      timestamp_data[j]['file'],
                                      relationship='similar_timestamp',
                                      time_diff=time_diff)
    
    def _correlate_software(self):
        """Find files created/modified with the same software."""
        software_map = defaultdict(list)
        
        for idx, metadata in enumerate(self.metadata_list):
            file_name = metadata.get('file_info', {}).get('name', f'file_{idx}')
            
            # Check various software fields
            software_names = set()
            
            # Image software
            img_meta = metadata.get('metadata', {}).get('exif', {})
            if img_meta.get('software', {}).get('software'):
                software_names.add(img_meta['software']['software'].lower().strip())
            
            # Document creator/producer
            doc = metadata.get('metadata', {}).get('document', {})
            if doc.get('creator'):
                software_names.add(doc['creator'].lower().strip())
            if doc.get('producer'):
                software_names.add(doc['producer'].lower().strip())
            
            # Web generator
            web = metadata.get('metadata', {}).get('web', {})
            if web.get('generator'):
                software_names.add(web['generator'].lower().strip())
            
            for software in software_names:
                software_map[software].append(file_name)
        
        # Create relationships
        for software, files in software_map.items():
            if len(files) > 1:
                self.relationships.append({
                    'type': 'shared_software',
                    'value': software,
                    'files': files,
                    'strength': 'medium'
                })
                for i in range(len(files)):
                    for j in range(i + 1, len(files)):
                        self.graph.add_edge(files[i], files[j],
                                          relationship='shared_software',
                                          value=software)
    
    def _correlate_hashes(self):
        """Find duplicate files based on hash values."""
        hash_map = defaultdict(list)
        
        for idx, metadata in enumerate(self.metadata_list):
            file_name = metadata.get('file_info', {}).get('name', f'file_{idx}')
            file_hash = metadata.get('file_info', {}).get('hash_sha256')
            
            if file_hash:
                hash_map[file_hash].append(file_name)
        
        # Create relationships for duplicates
        for file_hash, files in hash_map.items():
            if len(files) > 1:
                self.relationships.append({
                    'type': 'duplicate_files',
                    'value': file_hash[:16] + '...',
                    'files': files,
                    'strength': 'exact'
                })
                for i in range(len(files)):
                    for j in range(i + 1, len(files)):
                        self.graph.add_edge(files[i], files[j],
                                          relationship='duplicate',
                                          hash=file_hash)
    
    def _calculate_distance(self, lat1: float, lon1: float, 
                           lat2: float, lon2: float) -> float:
        """
        Calculate distance between two GPS coordinates using Haversine formula.
        
        Returns:
            Distance in kilometers
        """
        from math import radians, sin, cos, sqrt, atan2
        
        R = 6371  # Earth's radius in kilometers
        
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c
    
    def _build_summary(self) -> Dict[str, Any]:
        """Build correlation summary statistics."""
        summary = {
            'relationship_types': defaultdict(int),
            'most_connected_files': [],
            'isolated_files': []
        }
        
        # Count relationship types
        for rel in self.relationships:
            summary['relationship_types'][rel['type']] += 1
        
        # Find most connected files
        if self.graph.nodes():
            degree_dict = dict(self.graph.degree())
            sorted_nodes = sorted(degree_dict.items(), 
                                key=lambda x: x[1], reverse=True)
            summary['most_connected_files'] = [
                {'file': node, 'connections': degree} 
                for node, degree in sorted_nodes[:5]
            ]
            
            # Find isolated files (no connections)
            summary['isolated_files'] = [
                node for node, degree in degree_dict.items() if degree == 0
            ]
        
        return dict(summary)


