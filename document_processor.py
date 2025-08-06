import pandas as pd
import pdfplumber
import camelot
import tabula
import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import numpy as np

class DocumentProcessor:
    """
    Advanced PDF document processor for extracting tables from multifamily real estate documents.
    Supports multiple extraction methods for different PDF formats and table structures.
    """
    
    def __init__(self, debug=False):
        """Initialize the document processor with logging configuration."""
        self.debug = debug
        self.setup_logging()
        
        # Document type classification patterns
        self.doc_patterns = {
            'rent_roll': [
                r'rent\s*roll', r'unit\s*mix', r'tenant\s*roster', 
                r'lease\s*schedule', r'unit\s*type', r'monthly\s*rent'
            ],
            't12': [
                r't12', r'trailing\s*12', r'income\s*statement', 
                r'operating\s*statement', r'monthly\s*income', r'annual\s*statement'
            ],
            'offering_memorandum': [
                r'offering\s*memorandum', r'investment\s*summary', 
                r'property\s*overview', r'market\s*analysis'
            ]
        }
        
    def setup_logging(self):
        """Configure logging for debugging and error tracking."""
        logging.basicConfig(
            level=logging.DEBUG if self.debug else logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def classify_document(self, file_path: str) -> str:
        """
        Classify the document type based on content analysis.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Document type: 'rent_roll', 't12', 'offering_memorandum', or 'unknown'
        """
        try:
            with pdfplumber.open(file_path) as pdf:
                # Extract text from first few pages for classification
                text = ""
                for page_num in range(min(3, len(pdf.pages))):
                    text += pdf.pages[page_num].extract_text() or ""
                
                text = text.lower()
                
                # Score each document type based on keyword matches
                scores = {}
                for doc_type, patterns in self.doc_patterns.items():
                    score = sum(len(re.findall(pattern, text)) for pattern in patterns)
                    scores[doc_type] = score
                
                # Return the document type with highest score
                if max(scores.values()) > 0:
                    return max(scores, key=scores.get)
                else:
                    return 'unknown'
                    
        except Exception as e:
            self.logger.error(f"Error classifying document {file_path}: {str(e)}")
            return 'unknown'
    
    def extract_tables_multiple_methods(self, file_path: str) -> Dict[str, List[pd.DataFrame]]:
        """
        Extract tables using multiple methods and return the best results.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Dictionary with extraction method names as keys and list of DataFrames as values
        """
        results = {}
        
        # Method 1: pdfplumber (best for simple tables)
        results['pdfplumber'] = self._extract_with_pdfplumber(file_path)
        
        # Method 2: camelot (best for complex tables with borders)
        results['camelot'] = self._extract_with_camelot(file_path)
        
        # Method 3: tabula (good for various table formats)
        results['tabula'] = self._extract_with_tabula(file_path)
        
        return results
    
    def _extract_with_pdfplumber(self, file_path: str) -> List[pd.DataFrame]:
        """Extract tables using pdfplumber."""
        tables = []
        try:
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    page_tables = page.extract_tables()
                    for table_num, table in enumerate(page_tables):
                        if table and len(table) > 1:  # Ensure table has data
                            df = pd.DataFrame(table[1:], columns=table[0])
                            df = self._clean_dataframe(df)
                            if not df.empty:
                                df.attrs['page'] = page_num + 1
                                df.attrs['table'] = table_num + 1
                                df.attrs['method'] = 'pdfplumber'
                                tables.append(df)
                                
        except Exception as e:
            self.logger.error(f"pdfplumber extraction failed for {file_path}: {str(e)}")
            
        return tables
    
    def _extract_with_camelot(self, file_path: str) -> List[pd.DataFrame]:
        """Extract tables using camelot."""
        tables = []
        try:
            # Try lattice method first (for tables with borders)
            camelot_tables = camelot.read_pdf(file_path, flavor='lattice', pages='all')
            
            for table in camelot_tables:
                df = table.df
                df = self._clean_dataframe(df)
                if not df.empty:
                    df.attrs['page'] = table.page
                    df.attrs['method'] = 'camelot_lattice'
                    df.attrs['accuracy'] = table.accuracy
                    tables.append(df)
            
            # If lattice doesn't work well, try stream method
            if len(tables) == 0:
                camelot_tables = camelot.read_pdf(file_path, flavor='stream', pages='all')
                for table in camelot_tables:
                    df = table.df
                    df = self._clean_dataframe(df)
                    if not df.empty:
                        df.attrs['page'] = table.page
                        df.attrs['method'] = 'camelot_stream'
                        df.attrs['accuracy'] = table.accuracy
                        tables.append(df)
                        
        except Exception as e:
            self.logger.error(f"camelot extraction failed for {file_path}: {str(e)}")
            
        return tables
    
    def _extract_with_tabula(self, file_path: str) -> List[pd.DataFrame]:
        """Extract tables using tabula."""
        tables = []
        try:
            # Extract all tables from all pages
            tabula_tables = tabula.read_pdf(file_path, pages='all', multiple_tables=True)
            
            for table_num, df in enumerate(tabula_tables):
                df = self._clean_dataframe(df)
                if not df.empty:
                    df.attrs['table'] = table_num + 1
                    df.attrs['method'] = 'tabula'
                    tables.append(df)
                    
        except Exception as e:
            self.logger.error(f"tabula extraction failed for {file_path}: {str(e)}")
            
        return tables
    
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and normalize extracted DataFrame."""
        if df.empty:
            return df
            
        # Remove completely empty rows and columns
        df = df.dropna(how='all').dropna(axis=1, how='all')
        
        # Remove rows that are likely headers repeated in the middle
        df = self._remove_duplicate_headers(df)
        
        # Clean column names
        if not df.empty:
            df.columns = [self._clean_column_name(col) for col in df.columns]
        
        # Remove rows that are mostly empty (less than 30% filled)
        if not df.empty:
            threshold = max(1, int(len(df.columns) * 0.3))
            df = df.dropna(thresh=threshold)
        
        return df
    
    def _clean_column_name(self, col_name: str) -> str:
        """Clean and normalize column names."""
        if pd.isna(col_name) or col_name is None:
            return 'Unknown'
        
        col_name = str(col_name).strip()
        
        # Remove extra whitespace and special characters
        col_name = re.sub(r'\s+', ' ', col_name)
        col_name = re.sub(r'[^\w\s]', '', col_name)
        
        return col_name if col_name else 'Unknown'
    
    def _remove_duplicate_headers(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove rows that duplicate the header row."""
        if df.empty or len(df) < 2:
            return df
        
        header_row = df.iloc[0].astype(str).str.lower().str.strip()
        
        # Find rows that match the header
        duplicate_indices = []
        for idx in range(1, len(df)):
            row = df.iloc[idx].astype(str).str.lower().str.strip()
            if row.equals(header_row):
                duplicate_indices.append(idx)
        
        return df.drop(duplicate_indices)
    
    def get_best_extraction(self, results: Dict[str, List[pd.DataFrame]]) -> List[pd.DataFrame]:
        """
        Select the best extraction results based on quality metrics.
        
        Args:
            results: Dictionary of extraction results from different methods
            
        Returns:
            List of best DataFrames
        """
        all_tables = []
        
        for method, tables in results.items():
            for table in tables:
                # Calculate quality score
                score = self._calculate_table_quality_score(table)
                table.attrs['quality_score'] = score
                all_tables.append(table)
        
        # Sort by quality score and return top tables
        all_tables.sort(key=lambda x: x.attrs.get('quality_score', 0), reverse=True)
        
        # Group by page and return best table per page
        best_tables = {}
        for table in all_tables:
            page = table.attrs.get('page', 0)
            if page not in best_tables:
                best_tables[page] = table
        
        return list(best_tables.values())
    
    def _calculate_table_quality_score(self, df: pd.DataFrame) -> float:
        """Calculate a quality score for the extracted table."""
        if df.empty:
            return 0.0
        
        score = 0.0
        
        # Size score (bigger tables generally better, up to a point)
        size_score = min(len(df) * len(df.columns) / 100, 5.0)
        score += size_score
        
        # Data completeness score
        total_cells = len(df) * len(df.columns)
        filled_cells = df.count().sum()
        completeness_score = (filled_cells / total_cells) * 3.0
        score += completeness_score
        
        # Column structure score (prefer tables with reasonable number of columns)
        col_count = len(df.columns)
        if 3 <= col_count <= 15:
            score += 2.0
        elif col_count < 3:
            score -= 1.0
        
        # Method-specific bonuses
        method = df.attrs.get('method', '')
        if 'camelot' in method and df.attrs.get('accuracy', 0) > 80:
            score += 1.0
        
        return score
    
    def process_document(self, file_path: str) -> Dict[str, Any]:
        """
        Complete document processing pipeline.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Dictionary containing document type, extracted tables, and metadata
        """
        self.logger.info(f"Processing document: {file_path}")
        
        # Classify document
        doc_type = self.classify_document(file_path)
        self.logger.info(f"Document classified as: {doc_type}")
        
        # Extract tables using multiple methods
        extraction_results = self.extract_tables_multiple_methods(file_path)
        
        # Get best extraction results
        best_tables = self.get_best_extraction(extraction_results)
        
        # Prepare results
        result = {
            'file_path': file_path,
            'document_type': doc_type,
            'tables': best_tables,
            'extraction_summary': {
                'total_tables_found': len(best_tables),
                'methods_used': list(extraction_results.keys()),
                'tables_per_method': {method: len(tables) for method, tables in extraction_results.items()}
            }
        }
        
        # Add document-specific processing
        if doc_type == 'rent_roll':
            result.update(self._process_rent_roll_specific(best_tables))
        elif doc_type == 't12':
            result.update(self._process_t12_specific(best_tables))
        
        self.logger.info(f"Processing complete. Found {len(best_tables)} tables.")
        return result
    
    def _process_rent_roll_specific(self, tables: List[pd.DataFrame]) -> Dict[str, Any]:
        """Process rent roll specific data."""
        rent_roll_data = {}
        
        for table in tables:
            # Look for rent roll indicators
            columns = [col.lower() for col in table.columns]
            
            if any(keyword in ' '.join(columns) for keyword in ['unit', 'rent', 'tenant', 'lease']):
                rent_roll_data['main_table'] = table
                rent_roll_data['unit_count'] = len(table)
                rent_roll_data['columns_detected'] = table.columns.tolist()
                break
        
        return {'rent_roll_analysis': rent_roll_data}
    
    def _process_t12_specific(self, tables: List[pd.DataFrame]) -> Dict[str, Any]:
        """Process T12 specific data."""
        t12_data = {}
        
        for table in tables:
            # Look for financial statement indicators
            columns = [col.lower() for col in table.columns]
            
            if any(keyword in ' '.join(columns) for keyword in ['income', 'expense', 'total', 'month']):
                t12_data['main_table'] = table
                t12_data['rows_count'] = len(table)
                t12_data['columns_detected'] = table.columns.tolist()
                break
        
        return {'t12_analysis': t12_data}
    
    def save_results(self, results: Dict[str, Any], output_dir: str = 'outputs') -> Dict[str, str]:
        """Save extraction results to files."""
        Path(output_dir).mkdir(exist_ok=True)
        
        saved_files = {}
        base_name = Path(results['file_path']).stem
        
        # Save each table as CSV
        for idx, table in enumerate(results['tables']):
            filename = f"{base_name}_table_{idx+1}.csv"
            filepath = Path(output_dir) / filename
            table.to_csv(filepath, index=False)
            saved_files[f'table_{idx+1}'] = str(filepath)
        
        # Save summary report
        summary_file = Path(output_dir) / f"{base_name}_extraction_summary.txt"
        with open(summary_file, 'w') as f:
            f.write(f"Document Processing Summary\n")
            f.write(f"==========================\n\n")
            f.write(f"File: {results['file_path']}\n")
            f.write(f"Document Type: {results['document_type']}\n")
            f.write(f"Tables Found: {results['extraction_summary']['total_tables_found']}\n")
            f.write(f"Methods Used: {', '.join(results['extraction_summary']['methods_used'])}\n\n")
            
            for idx, table in enumerate(results['tables']):
                f.write(f"Table {idx+1}:\n")
                f.write(f"  - Shape: {table.shape}\n")
                f.write(f"  - Method: {table.attrs.get('method', 'unknown')}\n")
                f.write(f"  - Quality Score: {table.attrs.get('quality_score', 0):.2f}\n")
                f.write(f"  - Columns: {', '.join(table.columns)}\n\n")
        
        saved_files['summary'] = str(summary_file)
        return saved_files


# Example usage and testing
if __name__ == "__main__":
    # Initialize processor
    processor = DocumentProcessor(debug=True)
    
    # Example: Process a sample document
    sample_file = "sample_data/rent roll.pdf"  # Update with your file path
    
    try:
        results = processor.process_document(sample_file)
        
        print(f"Document Type: {results['document_type']}")
        print(f"Tables Found: {len(results['tables'])}")
        
        for idx, table in enumerate(results['tables']):
            print(f"\nTable {idx+1}:")
            print(f"Shape: {table.shape}")
            print(f"Method: {table.attrs.get('method', 'unknown')}")
            print(f"Columns: {table.columns.tolist()}")
            print(table.head())
        
        # Save results
        saved_files = processor.save_results(results)
        print(f"\nSaved files: {saved_files}")
        
    except Exception as e:
        print(f"Error processing document: {e}")