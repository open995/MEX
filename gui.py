#!/usr/bin/env python3
"""
MEX - Metadata Extractor
"""

import streamlit as st
import tempfile
import os
from pathlib import Path
import json

from mex.core import (
    ImageExtractor, DocumentExtractor, VideoExtractor,
    ArchiveExtractor, ExecutableExtractor, WebExtractor
)
from mex.correlate import MetadataCorrelator
from mex.analyze import AnomalyDetector
from mex.visualize import MetadataVisualizer
from mex.export import MetadataExporter


def extract_metadata(file_path: str):
    extractors = [
        ImageExtractor, DocumentExtractor, VideoExtractor,
        ArchiveExtractor, ExecutableExtractor, WebExtractor
    ]
    
    for extractor in extractors:
        if extractor.can_extract(file_path):
            return extractor.extract(file_path)
    return None


def main():
    st.set_page_config(
        page_title="MEX Platform",
        page_icon="⬡",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Working CSS
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        * {
            font-family: 'Inter', sans-serif;
        }
        
        /* Main background */
        .stApp {
            background: #000000;
        }
        
        /* Hide Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Headers */
        h1 {
            background: linear-gradient(90deg, #fff 0%, #c084fc 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 2rem;
            font-weight: 700;
        }
        
        h2, h3 {
            color: #ffffff;
        }
        
        /* Text */
        p, div, span, label {
            color: rgba(255, 255, 255, 0.7);
        }
        
        /* Buttons */
        .stButton > button {
            background: linear-gradient(90deg, rgba(147, 51, 234, 0.8) 0%, rgba(59, 130, 246, 0.8) 100%);
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 100px;
            padding: 0.5rem 2rem;
            font-weight: 500;
            transition: all 0.3s;
        }
        
        .stButton > button:hover {
            background: linear-gradient(90deg, rgb(147, 51, 234) 0%, rgb(59, 130, 246) 100%);
            border-color: rgba(255, 255, 255, 0.2);
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(147, 51, 234, 0.3);
        }
        
        /* File uploader */
        [data-testid="stFileUploader"] {
            background: rgba(255, 255, 255, 0.02);
            border: 2px dashed rgba(147, 51, 234, 0.4);
            border-radius: 12px;
            padding: 2rem;
        }
        
        [data-testid="stFileUploader"]:hover {
            border-color: rgba(147, 51, 234, 0.8);
            background: rgba(255, 255, 255, 0.04);
        }
        
        /* Metrics */
        [data-testid="stMetric"] {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            padding: 1rem;
        }
        
        [data-testid="stMetricLabel"] {
            color: rgba(255, 255, 255, 0.5);
            font-size: 0.75rem;
            text-transform: uppercase;
        }
        
        [data-testid="stMetricValue"] {
            color: #ffffff;
            font-size: 1.5rem;
            font-weight: 600;
        }
        
        /* Selectbox */
        .stSelectbox select {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            color: white;
            border-radius: 6px;
        }
        
        /* Checkbox */
        .stCheckbox label {
            color: rgba(255, 255, 255, 0.8);
        }
        
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .stTabs [data-baseweb="tab"] {
            color: rgba(255, 255, 255, 0.5);
            border-bottom: 2px solid transparent;
        }
        
        .stTabs [aria-selected="true"] {
            color: white;
            border-bottom-color: rgb(147, 51, 234);
        }
        
        /* Alerts */
        .stSuccess {
            background: rgba(34, 197, 94, 0.1);
            border: 1px solid rgba(34, 197, 94, 0.3);
            color: rgb(134, 239, 172);
        }
        
        .stInfo {
            background: rgba(59, 130, 246, 0.1);
            border: 1px solid rgba(59, 130, 246, 0.3);
            color: rgb(147, 197, 253);
        }
        
        .stError {
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.3);
            color: rgb(252, 165, 165);
        }
        
        /* Download button */
        .stDownloadButton > button {
            background: rgba(34, 197, 94, 0.2);
            color: rgb(134, 239, 172);
            border: 1px solid rgba(34, 197, 94, 0.3);
            border-radius: 100px;
        }
        
        /* JSON */
        .stJson {
            background: rgba(0, 0, 0, 0.5);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        /* Progress */
        .stProgress > div > div {
            background: linear-gradient(90deg, rgb(147, 51, 234), rgb(59, 130, 246));
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("# ⬡ MEX Platform")
    st.caption("Professional Metadata Extraction & Forensic Analysis")
    st.markdown("")
    
    # Controls
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        mode = st.selectbox("Mode", ["Analyze", "Batch", "Compare"], label_visibility="collapsed")
    with col2:
        correlate = st.checkbox("Correlation", value=True)
    with col3:
        detect = st.checkbox("Anomaly", value=True)
    
    st.markdown("---")
    
    # Main content
    if mode == "Analyze":
        uploaded = st.file_uploader(
            "Drop file here",
            type=['jpg', 'jpeg', 'png', 'pdf', 'docx', 'mp4', 'mp3', 'zip', 'exe', 'html'],
            label_visibility="collapsed"
        )
        
        if uploaded:
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded.name).suffix) as tmp:
                tmp.write(uploaded.getvalue())
                tmp_path = tmp.name
            
            with st.spinner("Analyzing..."):
                metadata = extract_metadata(tmp_path)
            
            if metadata:
                st.success("Complete")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Name", metadata['file_info']['name'][:15])
                with col2:
                    st.metric("Type", metadata['file_info']['type'])
                with col3:
                    size = metadata['file_info']['size']
                    st.metric("Size", f"{size/1024:.0f}KB" if size > 1024 else f"{size}B")
                with col4:
                    st.metric("Hash", metadata['file_info']['hash_sha256'][:8])
                
                st.markdown("")
                
                tab1, tab2 = st.tabs(["Data", "Export"])
                
                with tab1:
                    st.json(metadata)
                
                with tab2:
                    st.download_button(
                        "Download JSON",
                        json.dumps(metadata, indent=2, default=str),
                        f"{metadata['file_info']['name']}.json"
                    )
            
            os.unlink(tmp_path)
    
    elif mode == "Batch":
        files = st.file_uploader(
            "Drop files here",
            type=['jpg', 'jpeg', 'png', 'pdf', 'docx', 'mp4', 'mp3', 'zip', 'exe', 'html'],
            accept_multiple_files=True,
            label_visibility="collapsed"
        )
        
        if files and st.button("Process"):
            results = []
            progress = st.progress(0)
            
            for i, file in enumerate(files):
                with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.name).suffix) as tmp:
                    tmp.write(file.getvalue())
                    meta = extract_metadata(tmp.name)
                    if meta:
                        results.append(meta)
                    os.unlink(tmp.name)
                progress.progress((i + 1) / len(files))
            
            st.success(f"{len(results)} processed")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Files", len(results))
            with col2:
                st.metric("Types", len(set(m['file_info']['type'] for m in results)))
            with col3:
                total = sum(m['file_info']['size'] for m in results)
                st.metric("Total", f"{total/(1024*1024):.1f}MB")
            with col4:
                avg = total / len(results) if results else 0
                st.metric("Avg", f"{avg/1024:.0f}KB")
            
            if correlate:
                with st.spinner("Correlating..."):
                    correlator = MetadataCorrelator(results)
                    corr = correlator.correlate()
                
                if corr.get('total_relationships', 0) > 0:
                    with st.expander(f"Relationships ({corr['total_relationships']})"):
                        for r in corr.get('relationships', [])[:5]:
                            st.write(f"**{r['type']}** — {', '.join(r['files'][:2])}")
            
            if detect:
                with st.spinner("Detecting..."):
                    detector = AnomalyDetector(results)
                    anom = detector.analyze()
                
                if anom.get('anomalies'):
                    high = [a for a in anom['anomalies'] if a['severity'] == 'high']
                    if high:
                        with st.expander(f"Anomalies ({len(high)} critical)"):
                            for a in high[:3]:
                                st.error(f"**{a['file']}** — {a['description']}")
            
            st.download_button(
                "Download Report",
                json.dumps({'files': results}, indent=2, default=str),
                "report.json"
            )
    
    elif mode == "Compare":
        col1, col2 = st.columns(2)
        
        with col1:
            f1 = st.file_uploader("File 1", key="f1")
        with col2:
            f2 = st.file_uploader("File 2", key="f2")
        
        if f1 and f2 and st.button("Compare"):
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(f1.name).suffix) as t1:
                t1.write(f1.getvalue())
                m1 = extract_metadata(t1.name)
                os.unlink(t1.name)
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(f2.name).suffix) as t2:
                t2.write(f2.getvalue())
                m2 = extract_metadata(t2.name)
                os.unlink(t2.name)
            
            if m1['file_info']['hash_sha256'] == m2['file_info']['hash_sha256']:
                st.success("Identical")
            else:
                st.info("Different")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### File 1")
                st.json(m1)
            with col2:
                st.markdown("### File 2")
                st.json(m2)


if __name__ == '__main__':
    main()
