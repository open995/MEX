"""
Web/HTML metadata extractor for MEX.
Supports: HTML, HTM, and other web formats.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from bs4 import BeautifulSoup
import re

from mex.utils import (
    create_metadata_template,
    format_timestamp,
    compute_file_hash
)

logger = logging.getLogger(__name__)


class WebExtractor:
    """Extract metadata from web/HTML files."""
    
    SUPPORTED_FORMATS = {'.html', '.htm', '.xml'}
    
    @staticmethod
    def can_extract(file_path: str) -> bool:
        """Check if this extractor can handle the file."""
        return Path(file_path).suffix.lower() in WebExtractor.SUPPORTED_FORMATS
    
    @staticmethod
    def extract(file_path: str) -> Dict[str, Any]:
        """
        Extract metadata from HTML/web file.
        
        Args:
            file_path: Path to HTML file
            
        Returns:
            Metadata dictionary
        """
        metadata = create_metadata_template()
        path = Path(file_path)
        
        # Basic file info
        metadata['file_info'].update({
            'name': path.name,
            'path': str(path.absolute()),
            'size': path.stat().st_size,
            'type': 'web',
            'hash_md5': compute_file_hash(file_path, 'md5'),
            'hash_sha256': compute_file_hash(file_path, 'sha256')
        })
        
        # Timestamps
        stat = path.stat()
        metadata['timestamps'].update({
            'created': format_timestamp(stat.st_ctime),
            'modified': format_timestamp(stat.st_mtime),
            'accessed': format_timestamp(stat.st_atime)
        })
        
        # Extract HTML metadata
        web_data = WebExtractor._extract_html(file_path)
        
        if web_data:
            metadata['metadata']['web'] = web_data
        
        return metadata
    
    @staticmethod
    def _extract_html(file_path: str) -> Dict[str, Any]:
        """Extract metadata from HTML file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            soup = BeautifulSoup(content, 'html.parser')
            
            result = {
                'meta_tags': {},
                'opengraph': {},
                'twitter_card': {},
                'links': {},
                'scripts': [],
                'styles': []
            }
            
            # Extract title
            title = soup.find('title')
            if title:
                result['title'] = title.get_text().strip()
            
            # Extract all meta tags
            meta_tags = soup.find_all('meta')
            for meta in meta_tags:
                # Standard meta tags
                if meta.get('name'):
                    result['meta_tags'][meta.get('name')] = meta.get('content', '')
                
                # HTTP-equiv tags
                if meta.get('http-equiv'):
                    result['meta_tags'][f"http-equiv:{meta.get('http-equiv')}"] = meta.get('content', '')
                
                # OpenGraph tags
                if meta.get('property', '').startswith('og:'):
                    result['opengraph'][meta.get('property')] = meta.get('content', '')
                
                # Twitter Card tags
                if meta.get('name', '').startswith('twitter:'):
                    result['twitter_card'][meta.get('name')] = meta.get('content', '')
                
                # Charset
                if meta.get('charset'):
                    result['charset'] = meta.get('charset')
            
            # Extract common metadata fields
            common_fields = {
                'author': result['meta_tags'].get('author'),
                'description': result['meta_tags'].get('description'),
                'keywords': result['meta_tags'].get('keywords'),
                'generator': result['meta_tags'].get('generator'),
                'viewport': result['meta_tags'].get('viewport'),
                'robots': result['meta_tags'].get('robots')
            }
            result.update({k: v for k, v in common_fields.items() if v})
            
            # Extract links
            links = {
                'canonical': [],
                'alternate': [],
                'stylesheet': [],
                'icon': [],
                'other': []
            }
            
            for link in soup.find_all('link'):
                rel = link.get('rel', [''])[0] if isinstance(link.get('rel'), list) else link.get('rel', '')
                href = link.get('href', '')
                
                if rel == 'canonical':
                    links['canonical'].append(href)
                elif rel == 'alternate':
                    links['alternate'].append({
                        'href': href,
                        'type': link.get('type'),
                        'hreflang': link.get('hreflang')
                    })
                elif rel == 'stylesheet':
                    links['stylesheet'].append(href)
                elif rel in ['icon', 'shortcut icon', 'apple-touch-icon']:
                    links['icon'].append(href)
                else:
                    links['other'].append({'rel': rel, 'href': href})
            
            result['links'] = {k: v for k, v in links.items() if v}
            
            # Extract scripts
            scripts = []
            for script in soup.find_all('script', src=True):
                scripts.append(script.get('src'))
            result['scripts'] = scripts[:20]  # Limit to 20
            
            # Extract inline styles and stylesheets
            styles = []
            for style_link in soup.find_all('link', rel='stylesheet'):
                styles.append(style_link.get('href'))
            result['styles'] = styles[:20]  # Limit to 20
            
            # Extract structured data (JSON-LD)
            json_ld = []
            for script in soup.find_all('script', type='application/ld+json'):
                try:
                    import json
                    json_ld.append(json.loads(script.string))
                except:
                    pass
            if json_ld:
                result['structured_data'] = json_ld
            
            # Extract embedded images with metadata
            images = []
            for img in soup.find_all('img')[:10]:  # Limit to 10
                img_data = {
                    'src': img.get('src'),
                    'alt': img.get('alt'),
                    'title': img.get('title')
                }
                images.append({k: v for k, v in img_data.items() if v})
            if images:
                result['embedded_images'] = images
            
            # Detect CMS/framework
            cms_indicators = {
                'WordPress': ['wp-content', 'wp-includes'],
                'Drupal': ['drupal', 'sites/all'],
                'Joomla': ['joomla', 'com_content'],
                'React': ['react', 'react-dom'],
                'Angular': ['angular', 'ng-'],
                'Vue.js': ['vue.js', 'vue.min.js']
            }
            
            detected_cms = []
            content_lower = content.lower()
            for cms, indicators in cms_indicators.items():
                if any(indicator in content_lower for indicator in indicators):
                    detected_cms.append(cms)
            
            if detected_cms:
                result['detected_frameworks'] = detected_cms
            
            # Extract email addresses and URLs from comments
            comments = soup.find_all(string=lambda text: isinstance(text, str) and '<!--' in str(text))
            if comments:
                comment_text = ' '.join([str(c) for c in comments])
                emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', comment_text)
                if emails:
                    result['emails_in_comments'] = list(set(emails))[:5]  # Limit to 5 unique
            
            return result
            
        except Exception as e:
            logger.error(f"Error extracting HTML metadata: {e}")
            return {}


