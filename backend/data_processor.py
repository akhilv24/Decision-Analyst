"""
Data Processing Module
Handles data loading, validation, and cleaning of transaction datasets.
"""

import pandas as pd
import numpy as np
import re
import importlib
from datetime import datetime
import logging
import pdfplumber
from backend.csv_normalizer import normalize_any_csv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataProcessor:
    """Handles data loading, validation, and preprocessing."""
    
    REQUIRED_COLUMNS = ['date', 'amount']
    
    def __init__(self, file_path):
        """Initialize with file path."""
        self.file_path = file_path
        self.df = None
        self.original_shape = None
        self.processing_log = []
        self.last_error = None
    
    def load_file(self):
        """
        Load CSV or Excel file.
        
        Returns:
            pd.DataFrame or None if file loading fails
        """
        try:
            self.last_error = None
            lower_path = self.file_path.lower()
            if lower_path.endswith('.csv'):
                self.df = pd.read_csv(self.file_path)
            elif lower_path.endswith(('.xlsx', '.xls')):
                self.df = pd.read_excel(self.file_path)
            elif lower_path.endswith('.pdf'):
                self.df = self._load_pdf_file()
            elif lower_path.endswith(('.png', '.jpg', '.jpeg', '.webp')):
                self.df = self._load_image_file()
            else:
                logger.error(f"Unsupported file format: {self.file_path}")
                return None
            
            self.original_shape = self.df.shape
            logger.info(f"File loaded successfully. Shape: {self.original_shape}")
            self._log_process("File loaded", self.df.shape)
            return self.df
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error loading file: {str(e)}")
            return None

    def _looks_like_date(self, text):
        if not text:
            return False
        text = str(text).strip()
        patterns = [
            r'^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}$',
            r'^\d{4}[/-]\d{1,2}[/-]\d{1,2}$',
            r'^\d{1,2}\s+[A-Za-z]{3,9}\s+\d{2,4}$'
        ]
        return any(re.match(pattern, text) for pattern in patterns)

    def _parse_amount(self, raw_value):
        if raw_value is None:
            return None
        text = str(raw_value).strip()
        if not text:
            return None

        sign = -1 if ('(' in text and ')' in text) else 1
        text = text.replace('(', '').replace(')', '')
        text = re.sub(r'[^0-9.,\-]', '', text)
        text = text.replace(',', '')
        if text in {'', '-', '.', '-.'}:
            return None

        try:
            return float(text) * sign
        except ValueError:
            return None

    def _normalize_flow_type(self, value):
        if value is None:
            return None
        text = str(value).strip().lower()
        if not text:
            return None
        if any(token in text for token in ['credit', 'cr', 'deposit', 'received']):
            return 'credit'
        if any(token in text for token in ['debit', 'dr', 'withdraw', 'payment', 'check']):
            return 'debit'
        return None

    def _normalize_pdf_columns(self, df_pdf):
        col_map = {}
        for col in df_pdf.columns:
            key = str(col).strip().lower()
            if any(token in key for token in ['txn date', 'transaction date', 'value date', 'date']):
                col_map[col] = 'date'
            elif any(token in key for token in ['description', 'narration', 'remarks', 'particular']):
                col_map[col] = 'description'
            elif any(token in key for token in ['debit', 'withdrawal', 'paid out']):
                col_map[col] = 'debit'
            elif any(token in key for token in ['credit', 'deposit', 'paid in']):
                col_map[col] = 'credit'
            elif any(token in key for token in ['amount', 'amt']):
                col_map[col] = 'amount'

        if col_map:
            df_pdf = df_pdf.rename(columns=col_map)
        return df_pdf

    def _rows_from_pdf_tables(self):
        rows = []
        with pdfplumber.open(self.file_path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables() or []
                for table in tables:
                    if not table:
                        continue
                    header = [str(c).strip() if c else '' for c in table[0]]
                    data_rows = table[1:] if any('date' in h.lower() for h in header) else table
                    for row in data_rows:
                        if not row:
                            continue
                        cleaned = [str(cell).strip() if cell is not None else '' for cell in row]
                        if len(cleaned) < 2:
                            continue
                        rows.append(cleaned)
        return rows

    def _extract_statement_year(self, lines):
        for line in lines:
            match = re.search(r'Statement Date:\s*[A-Za-z]+\s+\d{1,2},\s*(\d{4})', line, re.IGNORECASE)
            if match:
                return int(match.group(1))
        return datetime.now().year

    def _looks_like_date_placeholder(self, text):
        if not text:
            return False
        cleaned = str(text).strip().lower().replace(' ', '')
        if self._looks_like_date(cleaned):
            return True
        if cleaned in {'mm/dd/yyyy', 'dd/mm/yyyy', 'yyyy/mm/dd', 'mm-dd-yyyy', 'dd-mm-yyyy'}:
            return True
        if '/' in cleaned and re.search(r'[a-z]', cleaned):
            # OCR often turns placeholders like mm/dd/yyyy into /pp/ww.
            return True
        return False

    def _parse_columnar_transactions(self, all_lines):
        """Parse OCR text when each transaction row is split into multiple lines."""
        rows = []
        if not all_lines:
            return rows

        lower_lines = [ln.lower().replace(' ', '') for ln in all_lines]
        start_idx = next((i for i, ln in enumerate(lower_lines) if 'transactions' in ln), None)
        if start_idx is None:
            return rows

        # Find header end (Date/Description/Credit/Debit/Balance) and start after it.
        idx = start_idx + 1
        while idx < len(all_lines) and any(h in lower_lines[idx] for h in ['date', 'description', 'credit', 'debit', 'balance']):
            idx += 1

        statement_year = self._extract_statement_year(all_lines)
        base_date = datetime(statement_year, 1, 1)
        txn_counter = 0

        while idx < len(all_lines):
            line = all_lines[idx].strip()
            lower = line.lower().replace(' ', '')
            if not line:
                idx += 1
                continue
            if 'endoftransactions' in lower or 'total' in lower or 'templatelab.com' in lower:
                break

            date_token = None
            if self._looks_like_date_placeholder(line):
                date_token = line
                idx += 1
                if idx >= len(all_lines):
                    break
                line = all_lines[idx].strip()
                lower = line.lower().replace(' ', '')

            if not line or re.search(r'\d', line):
                idx += 1
                continue

            description = line
            idx += 1

            amount_values = []
            while idx < len(all_lines):
                look = all_lines[idx].strip()
                look_lower = look.lower().replace(' ', '')
                if not look:
                    idx += 1
                    continue
                if self._looks_like_date_placeholder(look) or 'endoftransactions' in look_lower:
                    break
                parsed_amount = self._parse_amount(look)
                if parsed_amount is not None:
                    amount_values.append(abs(float(parsed_amount)))
                    idx += 1
                    continue
                if re.search(r'[a-z]', look_lower):
                    break
                idx += 1

            if not amount_values:
                continue

            desc_lower = description.lower()
            if any(token in desc_lower for token in ['payment', 'debit', 'transfer out', 'loan', 'utility', 'withdraw', 'card']):
                txn_type = 'debit'
                amount = amount_values[0]
            elif any(token in desc_lower for token in ['transfer in', 'deposit', 'refund', 'salary', 'received']):
                txn_type = 'credit'
                amount = amount_values[0]
            elif len(amount_values) >= 2:
                # Typical row has txn amount + running balance; transaction amount is first number.
                txn_type = 'debit'
                amount = amount_values[0]
            else:
                txn_type = 'debit'
                amount = amount_values[0]

            if date_token and self._looks_like_date(date_token):
                date_value = date_token
            else:
                date_value = (base_date + pd.to_timedelta(txn_counter, unit='D')).strftime('%Y-%m-%d')

            rows.append({
                'date': date_value,
                'description': description,
                'amount': amount,
                'type': txn_type,
            })
            txn_counter += 1

            if idx < len(all_lines) and self._looks_like_date_placeholder(all_lines[idx]):
                continue

        return rows

    def _parse_statement_lines(self, all_lines):
        """Parse statement-like text lines into transaction rows."""
        rows = []
        if not all_lines:
            return rows

        statement_year = self._extract_statement_year(all_lines)
        section_type = None
        pending_desc = []

        for line in all_lines:
            lower = line.lower()

            if 'deposits & other credits account' in lower or 'transactions' in lower:
                section_type = section_type or 'debit'
                pending_desc = []
            if any(token in lower for token in ['deposits & other credits account', 'credit amount']):
                section_type = 'credit'
                pending_desc = []
                continue
            if any(token in lower for token in [
                'atm withdrawals & debits account',
                'checks paid account',
                'checkspaid account',
                'withdrawals & other debits account',
                'visa check card purchases & debits account',
                'debit amount',
            ]):
                section_type = 'debit'
                pending_desc = []
                continue

            if lower.startswith('total ') or 'end of transactions' in lower:
                pending_desc = []
                continue

            if 'description' in lower and 'amount' in lower:
                continue

            check_line_match = re.match(r'^\s*(\d{2}[/-]\d{2})\s+(\d{3,6})\s+(\$?\d[\d,]*\.\d{2})\b', line)
            if check_line_match and section_type == 'debit':
                date_token = check_line_match.group(1).replace('/', '-')
                check_number = check_line_match.group(2)
                amount_value = self._parse_amount(check_line_match.group(3))
                if amount_value is not None:
                    rows.append({
                        'date': f"{date_token}-{statement_year}",
                        'description': f"Check #{check_number}",
                        'amount': abs(float(amount_value)),
                        'type': 'debit'
                    })
                    pending_desc = []
                    continue

            date_match = re.search(r'\b(\d{2}[/-]\d{2}(?:[/-]\d{2,4})?)\b', line)
            amount_matches = re.findall(r'\$?\d[\d,]*\.\d{2}', line)

            if date_match and amount_matches:
                date_token = date_match.group(1).replace('/', '-')
                if date_token.count('-') == 1:
                    date_token = f"{date_token}-{statement_year}"

                amount_values = [self._parse_amount(a) for a in amount_matches]
                amount_values = [abs(float(v)) for v in amount_values if v is not None]
                if not amount_values:
                    pending_desc.append(line)
                    continue

                amount = amount_values[0]
                transaction_type = section_type or 'debit'
                if len(amount_values) >= 2 and section_type is None:
                    # Generic statement table: first numeric is credit, second is debit.
                    credit_candidate = amount_values[0]
                    debit_candidate = amount_values[1]
                    if credit_candidate > 0 and debit_candidate > 0:
                        amount = credit_candidate if 'transfer in' in lower or 'deposit' in lower else debit_candidate
                        transaction_type = 'credit' if amount == credit_candidate else 'debit'

                line_wo_amounts = line
                for amt in amount_matches:
                    line_wo_amounts = line_wo_amounts.replace(amt, ' ')
                line_wo_date = line_wo_amounts.replace(date_match.group(1), ' ').strip()
                line_wo_ref = re.sub(r'\b\d{8,}\b', '', line_wo_date).strip()
                line_wo_extra_date = re.sub(r'\b\d{2}[/-]\d{2}(?:[/-]\d{2,4})?\b', '', line_wo_ref).strip()
                line_wo_check_no = re.sub(r'\b\d{3,6}\b', '', line_wo_extra_date).strip()

                description_parts = [d for d in pending_desc if d]
                if line_wo_check_no:
                    description_parts.append(line_wo_check_no)

                description = ' '.join(description_parts).strip() or 'Bank transaction'
                desc_lower = description.lower()
                if any(token in desc_lower for token in ['payment', 'transfer out', 'withdraw', 'loan', 'card bill', 'utility']):
                    transaction_type = 'debit'
                elif any(token in desc_lower for token in ['salary', 'neft cr', 'imps cr', 'refund', 'transfer in', 'deposit', 'received']):
                    transaction_type = 'credit'

                rows.append({
                    'date': date_token,
                    'description': description,
                    'amount': amount,
                    'type': transaction_type
                })

                pending_desc = []
                continue

            if section_type and len(line) <= 100 and not any(ch.isdigit() for ch in line[-6:]):
                if not any(noise in lower for noise in [
                    'account #', 'page number', 'statement date', 'beginning balance', 'ending balance',
                    'date paid check number amount reference number'
                ]):
                    pending_desc.append(line)

        if not rows:
            rows = self._parse_columnar_transactions(all_lines)

        return rows

    def _rows_from_pdf_text(self):
        """Extract transactions from text-based bank statement PDFs."""
        with pdfplumber.open(self.file_path) as pdf:
            all_lines = []
            for page in pdf.pages:
                page_text = page.extract_text() or ''
                all_lines.extend([ln.strip() for ln in page_text.splitlines() if ln and ln.strip()])
        return self._parse_statement_lines(all_lines)

    def _lines_from_image_ocr(self):
        pil_image_module = None
        pytesseract_module = None
        try:
            pil_image_module = importlib.import_module('PIL.Image')
            pytesseract_module = importlib.import_module('pytesseract')
        except ModuleNotFoundError:
            pil_image_module = None
            pytesseract_module = None

        # Preferred OCR path: Tesseract (high accuracy on statement tables)
        if pil_image_module is not None and pytesseract_module is not None:
            try:
                image = pil_image_module.open(self.file_path)
            except Exception as exc:
                raise ValueError(f'Could not open image file: {exc}') from exc

            ocr_config_candidates = ['--psm 6', '--psm 11']
            best_lines = []
            for cfg in ocr_config_candidates:
                try:
                    text = pytesseract_module.image_to_string(image, config=cfg)
                except Exception:
                    break
                lines = [ln.strip() for ln in (text or '').splitlines() if ln and ln.strip()]
                if len(lines) > len(best_lines):
                    best_lines = lines

            if best_lines:
                return best_lines

        # Fallback OCR path: RapidOCR (no system-level Tesseract dependency)
        try:
            rapidocr_module = importlib.import_module('rapidocr_onnxruntime')
            ocr_engine = rapidocr_module.RapidOCR()
            ocr_result, _ = ocr_engine(self.file_path)
            if not ocr_result:
                return []
            raw_lines = [item[1] for item in ocr_result if item and len(item) >= 2]
            return [ln.strip() for ln in raw_lines if ln and str(ln).strip()]
        except ModuleNotFoundError as exc:
            raise ValueError(
                'Image OCR is unavailable. Install pytesseract + Pillow + Tesseract OCR, or rapidocr-onnxruntime.'
            ) from exc
        except Exception as exc:
            raise ValueError(
                'OCR failed for this image. Try a clearer image or install Tesseract OCR for better results.'
            ) from exc

    def _load_image_file(self):
        """Parse bank statement images (JPG/PNG) via OCR."""
        all_lines = self._lines_from_image_ocr()
        rows = self._parse_statement_lines(all_lines)

        if not rows:
            raise ValueError(
                'Unable to extract transactions from image. Use a clear, high-resolution statement image with visible date/amount columns.'
            )

        df_img = pd.DataFrame(rows)
        df_img = self._normalize_pdf_columns(df_img)
        return df_img

    def _load_pdf_file(self):
        """Parse bank statement PDFs into a transaction dataframe."""
        try:
            rows = self._rows_from_pdf_tables()
        except Exception as e:
            logger.error(f"Error reading PDF tables: {str(e)}")
            rows = []

        if not rows:
            try:
                text_rows = self._rows_from_pdf_text()
                rows = [[
                    item.get('date', ''),
                    item.get('description', ''),
                    item.get('amount', ''),
                    item.get('type', ''),
                ] for item in text_rows]
            except Exception as e:
                logger.error(f"Error reading PDF text rows: {str(e)}")
                rows = []

        parsed = []
        for row in rows:
            date_idx = next((i for i, cell in enumerate(row) if self._looks_like_date(cell)), None)
            if date_idx is None:
                continue

            date_text = row[date_idx]
            description = ''
            if len(row) > date_idx + 1:
                description = row[date_idx + 1]

            debit_candidates = [self._parse_amount(c) for c in row[date_idx + 2:date_idx + 5]]
            debit_candidates = [abs(v) for v in debit_candidates if v is not None]
            amount = debit_candidates[0] if debit_candidates else None
            txn_type = 'debit'

            explicit_type = None
            if len(row) > date_idx + 3:
                explicit_type = self._normalize_flow_type(row[date_idx + 3])
            if explicit_type in {'credit', 'debit'}:
                txn_type = explicit_type

            if amount is None:
                all_amounts = [self._parse_amount(c) for c in row if self._parse_amount(c) is not None]
                if not all_amounts:
                    continue
                amount = abs(all_amounts[-1])
                txn_type = explicit_type or 'debit'

            desc_lower = str(description).lower()
            if any(token in desc_lower for token in ['salary', 'neft cr', 'imps cr', 'credit', 'refund', 'received']):
                txn_type = 'credit'

            parsed.append({
                'date': date_text,
                'description': description or 'Bank transaction',
                'amount': amount,
                'type': txn_type
            })

        df_pdf = pd.DataFrame(parsed)
        if df_pdf.empty:
            raise ValueError('Unable to extract transaction rows from PDF. Please upload CSV/Excel or a table-based statement PDF.')

        df_pdf = self._normalize_pdf_columns(df_pdf)
        return df_pdf
    
    def standardize_columns(self):
        """
        Standardize column names to lowercase and handle common variations.
        """
        if self.df is None:
            return False
        
        # Mapping of common variations
        column_mapping = {
            'Date': 'date',
            'Amount': 'amount',
            'Description': 'description',
            'Category': 'category',
            'Merchant': 'merchant',
            'Type': 'type',
            'Transaction Date': 'date',
            'Transaction Amount': 'amount',
        }
        
        # Normalize column names
        for old_col in self.df.columns:
            if old_col in column_mapping:
                self.df.rename(columns={old_col: column_mapping[old_col]}, inplace=True)
        
        # Convert all to lowercase
        self.df.columns = [col.lower() for col in self.df.columns]
        self._log_process("Columns standardized", self.df.shape)
        return True
    
    def handle_missing_values(self, strategy='remove'):
        """
        Handle missing values in the dataset.
        
        Args:
            strategy (str): 'remove' or 'forward_fill'
        """
        if self.df is None:
            return False
        
        initial_rows = len(self.df)
        
        if strategy == 'remove':
            # Only drop on columns that actually exist
            subset_cols = [c for c in ['date', 'amount'] if c in self.df.columns]
            if subset_cols:
                self.df = self.df.dropna(subset=subset_cols)
        elif strategy == 'forward_fill':
            self.df = self.df.ffill()
        
        removed_rows = initial_rows - len(self.df)
        logger.info(f"Missing values handled. Rows removed: {removed_rows}")
        self._log_process(f"Missing values handled ({strategy})", self.df.shape)
        return True
    
    def remove_duplicates(self):
        """
        Remove duplicate transactions based on date, amount, and description.
        """
        if self.df is None:
            return False
        
        initial_rows = len(self.df)
        
        # Define subset for duplicate checking
        subset_cols = [col for col in ['date', 'amount', 'description'] if col in self.df.columns]
        # Pandas raises ValueError on subset=[], so fall back to full-row duplicate removal.
        if subset_cols:
            self.df = self.df.drop_duplicates(subset=subset_cols, keep='first')
        else:
            self.df = self.df.drop_duplicates(keep='first')
        
        removed_rows = initial_rows - len(self.df)
        logger.info(f"Duplicates removed: {removed_rows}")
        self._log_process("Duplicates removed", self.df.shape)
        return True
    
    def standardize_date_format(self):
        """
        Standardize date column to datetime format.
        """
        if self.df is None or 'date' not in self.df.columns:
            return False
        
        try:
            self.df['date'] = pd.to_datetime(self.df['date'])
            self.df = self.df.sort_values('date').reset_index(drop=True)
            logger.info("Date format standardized and sorted")
            self._log_process("Date format standardized", self.df.shape)
            return True
        except Exception as e:
            logger.error(f"Error standardizing date format: {str(e)}")
            return False
    
    def standardize_amount_format(self):
        """
        Standardize amount column to numeric format.
        """
        if self.df is None or 'amount' not in self.df.columns:
            return False
        
        try:
            # Remove currency symbols and convert to float
            self.df['amount'] = (self.df['amount'].astype(str)
                                 .str.replace('$',  '', regex=False)
                                 .str.replace('₹',  '', regex=False)
                                 .str.replace(',',  '', regex=False)
                                 .str.strip())
            self.df['amount'] = pd.to_numeric(self.df['amount'], errors='coerce')
            self.df = self.df.dropna(subset=['amount'])
            logger.info("Amount format standardized")
            self._log_process("Amount format standardized", self.df.shape)
            return True
        except Exception as e:
            logger.error(f"Error standardizing amount format: {str(e)}")
            return False
    
    def clean_data(self):
        """
        Execute full data cleaning pipeline.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if self.df is None:
            return False
        
        logger.info("Starting data cleaning pipeline...")
        
        self.standardize_columns()
        self.handle_missing_values()
        self.remove_duplicates()
        self.standardize_date_format()
        self.standardize_amount_format()
        
        logger.info(f"Data cleaning completed. Final shape: {self.df.shape}")
        return True
    
    def validate_required_columns(self):
        """Validate required columns."""
        required = ['date', 'amount']
        missing = [c for c in required if c not in self.df.columns]

        if missing:
            # Fallback: auto-map any schema
            pack = normalize_any_csv(self.df)
            ndf = pack.get("data")
            if ndf is not None and not ndf.empty and all(col in ndf.columns for col in required):
                self.df = ndf
                logger.info("Auto-normalization applied. Required columns mapped successfully.")
                return True

            raise ValueError(missing)

        return True
    
    def get_data_quality_report(self):
        """
        Generate a data quality report.
        
        Returns:
            dict: Data quality metrics
        """
        if self.df is None:
            return {}
        
        # Convert missing values to serializable format
        missing_values = self.df.isnull().sum().to_dict()
        missing_values = {k: int(v) for k, v in missing_values.items()}

        total_cells = int(len(self.df) * len(self.df.columns))
        missing_cells = int(sum(missing_values.values()))
        quality_pct = round(((total_cells - missing_cells) / total_cells) * 100, 1) if total_cells else 0.0

        currency_labels = {
            '₹': 'INR (₹)',
            '$': 'USD ($)',
            '€': 'EUR (€)',
            '£': 'GBP (£)'
        }
        detected_currency = 'Not detected'
        try:
            with open(self.file_path, 'rb') as f:
                raw_sample = f.read(15000)
            decoded_sample = raw_sample.decode('utf-8', errors='ignore')
            for symbol, label in currency_labels.items():
                if symbol in decoded_sample:
                    detected_currency = label
                    break
        except Exception:
            detected_currency = 'Not detected'

        anomaly_prescan_count = 0
        if 'amount' in self.df.columns:
            amount_series = pd.to_numeric(self.df['amount'], errors='coerce').dropna()
            if len(amount_series) >= 4:
                q1 = float(amount_series.quantile(0.25))
                q3 = float(amount_series.quantile(0.75))
                iqr = q3 - q1
                lower = q1 - (1.5 * iqr)
                upper = q3 + (1.5 * iqr)
                anomaly_prescan_count = int(((amount_series < lower) | (amount_series > upper)).sum())
        
        return {
            'total_records': int(len(self.df)),
            'total_columns': int(len(self.df.columns)),
            'columns': list(self.df.columns),
            'date_range': f"{self.df['date'].min()} to {self.df['date'].max()}" if 'date' in self.df.columns else 'N/A',
            'date_range_start': str(self.df['date'].min()) if 'date' in self.df.columns else None,
            'date_range_end': str(self.df['date'].max()) if 'date' in self.df.columns else None,
            'missing_values': missing_values,
            'missing_cells': missing_cells,
            'missing_total': missing_cells,
            'data_quality_pct': quality_pct,
            'quality_score': quality_pct,
            'duplicate_rows': int(self.df.duplicated().sum()),
            'currency': detected_currency,
            'anomaly_prescan_count': anomaly_prescan_count,
            'amount_stats': {
                'min': float(self.df['amount'].min()) if 'amount' in self.df.columns else None,
                'max': float(self.df['amount'].max()) if 'amount' in self.df.columns else None,
                'mean': float(self.df['amount'].mean()) if 'amount' in self.df.columns else None,
                'total': float(self.df['amount'].sum()) if 'amount' in self.df.columns else None,
            }
        }
    
    def _log_process(self, step, shape):
        """Log processing step."""
        self.processing_log.append({
            'step': step,
            'timestamp': datetime.now().isoformat(),
            'shape': shape
        })
    
    def export_cleaned_data(self, output_path):
        """Export cleaned data to CSV."""
        if self.df is None:
            return False
        
        try:
            self.df.to_csv(output_path, index=False)
            logger.info(f"Data exported to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error exporting data: {str(e)}")
            return False
