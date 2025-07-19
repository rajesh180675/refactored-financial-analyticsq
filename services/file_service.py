import io
import logging
import pandas as pd
import zipfile
import tempfile
import shutil
from pathlib import Path
from typing import List, Tuple, Optional
import streamlit as st


class FileService:
    def __init__(self, config_manager, state_manager, event_system):
        self.config = config_manager
        self.state = state_manager
        self.events = event_system
        self.logger = logging.getLogger(__name__)
        self.temp_dirs = []

    def __del__(self):
        self.cleanup_temp_dirs()

    def cleanup_temp_dirs(self):
        for temp_dir in self.temp_dirs:
            try:
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
            except Exception as e:
                self.logger.error(f"Error cleaning up temp dir: {e}")
        self.temp_dirs.clear()

    def process_uploaded_files(self, uploaded_files: List[st.runtime.uploaded_file_manager.UploadedFile]) -> Optional[pd.DataFrame]:
        try:
            self.events.publish("file_processing_started", {"count": len(uploaded_files)}, "FileService")
            
            all_dataframes = []
            
            for file in uploaded_files:
                try:
                    if file.name.lower().endswith(('.zip', '.7z')):
                        extracted_dfs = self._process_compressed_file(file)
                        all_dataframes.extend(extracted_dfs)
                    else:
                        df = self._parse_single_file(file)
                        if df is not None:
                            all_dataframes.append(df)
                            
                except Exception as e:
                    self.logger.error(f"Error processing {file.name}: {e}")
                    continue
            
            if all_dataframes:
                # Merge all dataframes
                data_service = self.state.get('data_service')
                if data_service:
                    merged_df = data_service.merge_dataframes(all_dataframes)
                    
                    self.events.publish("file_processing_completed", 
                                      {"dataframes": len(all_dataframes)}, 
                                      "FileService")
                    
                    return merged_df
                else:
                    self.logger.error("Data service not available")
                    return None
            else:
                self.logger.warning("No valid dataframes extracted")
                return None
                
        except Exception as e:
            self.logger.error(f"File processing failed: {e}")
            self.events.publish("file_processing_failed", {"error": str(e)}, "FileService")
            return None
        finally:
            self.cleanup_temp_dirs()

    def _process_compressed_file(self, file) -> List[pd.DataFrame]:
        dataframes = []
        temp_dir = Path(tempfile.mkdtemp())
        self.temp_dirs.append(temp_dir)
        
        try:
            # Save uploaded file to temp location
            temp_file = temp_dir / file.name
            with open(temp_file, 'wb') as f:
                f.write(file.getbuffer())
            
            if file.name.lower().endswith('.zip'):
                extracted_files = self._extract_zip(temp_file, temp_dir)
            elif file.name.lower().endswith('.7z'):
                extracted_files = self._extract_7z(temp_file, temp_dir)
            else:
                return []
            
            # Parse each extracted file
            for filename, content in extracted_files:
                df = self._parse_file_content(filename, content)
                if df is not None:
                    dataframes.append(df)
            
            return dataframes
            
        except Exception as e:
            self.logger.error(f"Error processing compressed file: {e}")
            return []

    def _extract_zip(self, zip_path: Path, temp_dir: Path) -> List[Tuple[str, bytes]]:
        extracted = []
        
        with zipfile.ZipFile(zip_path, 'r') as zip_file:
            supported_extensions = ['.csv', '.html', '.htm', '.xls', '.xlsx']
            
            for file_name in zip_file.namelist():
                if any(file_name.lower().endswith(ext) for ext in supported_extensions):
                    try:
                        content = zip_file.read(file_name)
                        clean_name = Path(file_name).name
                        extracted.append((clean_name, content))
                    except Exception as e:
                        self.logger.error(f"Error extracting {file_name}: {e}")
        
        return extracted

    def _extract_7z(self, seven_zip_path: Path, temp_dir: Path) -> List[Tuple[str, bytes]]:
        extracted = []
        
        try:
            import py7zr
            
            with py7zr.SevenZipFile(seven_zip_path, mode='r') as seven_zip:
                seven_zip.extractall(path=temp_dir)
                
                supported_extensions = ['.csv', '.html', '.htm', '.xls', '.xlsx']
                
                for extracted_file in temp_dir.rglob('*'):
                    if extracted_file.is_file():
                        if any(extracted_file.name.lower().endswith(ext) for ext in supported_extensions):
                            try:
                                with open(extracted_file, 'rb') as f:
                                    content = f.read()
                                extracted.append((extracted_file.name, content))
                            except Exception as e:
                                self.logger.error(f"Error reading {extracted_file}: {e}")
                                
        except ImportError:
            self.logger.error("py7zr not installed. Cannot extract 7z files.")
        except Exception as e:
            self.logger.error(f"Error extracting 7z file: {e}")
        
        return extracted

    def _parse_single_file(self, file) -> Optional[pd.DataFrame]:
        try:
            file_content = file.read()
            file.seek(0)
            return self._parse_file_content(file.name, file_content)
        except Exception as e:
            self.logger.error(f"Error parsing {file.name}: {e}")
            return None

    def _parse_file_content(self, filename: str, content: bytes) -> Optional[pd.DataFrame]:
        try:
            file_ext = Path(filename).suffix.lower()
            
            # Check if content is HTML
            sample = content[:1024].decode('utf-8', errors='ignore')
            
            if '<html' in sample.lower() or '<table' in sample.lower():
                return self._parse_html_content(content)
            elif file_ext == '.csv':
                return self._parse_csv_content(content)
            elif file_ext in ['.xls', '.xlsx']:
                return self._parse_excel_content(content, file_ext)
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Error parsing file content: {e}")
            return None

    def _parse_html_content(self, content: bytes) -> Optional[pd.DataFrame]:
        try:
            tables = pd.read_html(io.BytesIO(content))
            if tables:
                df = max(tables, key=len)
                
                # Clean up multi-level headers
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = [' >> '.join(str(level).strip() for level in col if str(level) != 'nan').strip(' >> ') 
                                 for col in df.columns]
                
                # Set index
                potential_index_cols = ['Particulars', 'Description', 'Items', 'Metric']
                for col in potential_index_cols:
                    matching_cols = [c for c in df.columns if col.lower() in c.lower()]
                    if matching_cols:
                        df = df.set_index(matching_cols[0])
                        break
                
                return df
        except Exception as e:
            self.logger.error(f"HTML parsing failed: {e}")
            return None

    def _parse_csv_content(self, content: bytes) -> Optional[pd.DataFrame]:
        try:
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    df = pd.read_csv(io.BytesIO(content), encoding=encoding, index_col=0)
                    return df
                except UnicodeDecodeError:
                    continue
            return None
        except Exception as e:
            self.logger.error(f"CSV parsing failed: {e}")
            return None

    def _parse_excel_content(self, content: bytes, file_ext: str) -> Optional[pd.DataFrame]:
        try:
            engines = ['openpyxl', 'xlrd'] if file_ext == '.xlsx' else ['xlrd']
            
            for engine in engines:
                try:
                    df = pd.read_excel(io.BytesIO(content), index_col=0, engine=engine)
                    if not df.empty:
                        return df
                except Exception:
                    continue
            
            # Try HTML parsing as fallback for .xls files
            try:
                tables = pd.read_html(io.BytesIO(content))
                if tables:
                    return self._clean_html_table(max(tables, key=len))
            except:
                pass
            
            return None
        except Exception as e:
            self.logger.error(f"Excel parsing failed: {e}")
            return None

    def _clean_html_table(self, df: pd.DataFrame) -> pd.DataFrame:
        # Clean column names
        df.columns = [str(col).strip() for col in df.columns]
        
        # Remove unnamed columns
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        
        # Set appropriate index
        if len(df.columns) > 0 and df.iloc[:, 0].dtype == object:
            df = df.set_index(df.columns[0])
        
        return df
