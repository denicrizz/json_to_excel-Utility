# 📊 JSON → Excel Transformer - Integration Guide

## Overview
Proyek ini mengintegrasikan tiga komponen utama untuk mengubah file JSON menjadi file Excel dengan benar.

---

## Arsitektur Sistem

### 1. **app.py** (Streamlit UI)
Antarmuka web untuk user
- Upload template.json
- Upload multiple answer JSON files
- Menampilkan progress processing
- Download hasil Excel

**Dependencies:**
- `streamlit`
- Import: `cleaning.process_files`, `json_to_excel.create_excel`

### 2. **cleaning.py** (Data Processing)
Melakukan cleaning dan transformasi data JSON

**Fungsi Utama:**
- `process_files(template_path, input_dir, output_file)` - Main processing function
  - Membaca template dan semua answer JSON
  - Melakukan cleaning data
  - Mengorganisir data ke principal, main tables, dan nested tables
  - Return: dict dengan struktur data yang sudah dibersihkan

**Helper Functions:**
- `process_file()` - Process satu file JSON
- `extract_data()` - Extract data dari answer JSON
- `find_blocks()` - Cari blok type:1 dari template
- `create_mapping()` - Mapping datakey ke blok
- `clean_value()` - Bersihkan value (string, number, list, dict)
- `parse_json()` - Parse JSON string to object
- `is_dropdown()` - Deteksi dropdown field

**Dependencies:**
- `json`, `re`, `pathlib`, `collections`

### 3. **json_to_excel.py** (Excel Export)
Mengexport cleaned data ke file Excel

**Fungsi Utama:**
- `create_excel(cleaned_data, output_file)` - Export data to Excel
  - Input: cleaned_data dari process_files()
  - Output: .xlsx file dengan multiple sheets
  - Menangani principal data, main tables, nested tables
  - Validasi cell yang terlalu panjang (>32767 chars)

**Helper Functions:**
- `load_data()` - Load JSON file
- `make_dataframe()` - Convert dict/list ke pandas DataFrame
- `clean_sheet_name()` - Bersihkan nama sheet
- `unique_sheet_name()` - Avoid duplicate sheet names
- `check_long_cells()` - Validasi panjang cell

**Dependencies:**
- `json`, `re`, `pathlib`, `pandas`, `openpyxl`

---

## Workflow Program

```
┌─────────────────────────────────────────────────────────────┐
│                    STREAMLIT UI (app.py)                     │
│  - Upload template.json                                     │
│  - Upload answer JSON files (max 50)                        │
│  - Button: "🚀 Proses JSON"                                 │
└─────────────┬───────────────────────────────────────────────┘
              │
              ├─► Create temp directory
              │
              ├─► Save template & answer files
              │
              │
              ▼
┌─────────────────────────────────────────────────────────────┐
│              CLEANING PROCESS (cleaning.py)                 │
│  - Load template.json                                       │
│  - Find blocks (type:1) dari template                       │
│  - Create field mapping                                     │
│  - For each answer JSON:                                    │
│    • Extract principal data                                 │
│    • Extract main tables                                    │
│    • Extract nested tables                                  │
│  - Clean all values                                         │
│  - Save to data_clean.json                                  │
│  - Return cleaned_data dict                                 │
└─────────────┬───────────────────────────────────────────────┘
              │
              │ cleaned_data = {
              │   "principal data": [...],
              │   "tables": {...},
              │   "nested": {...}
              │ }
              │
              ▼
┌─────────────────────────────────────────────────────────────┐
│              EXCEL EXPORT (json_to_excel.py)                │
│  - Create Excel file with openpyxl                          │
│  - Sheet 1: Principal Data                                  │
│  - Sheet 2-N: Main Tables (1 per table)                     │
│  - Sheet N+1-M: Nested Tables (1 per table)                 │
│  - Validate cell content (max 32767 chars)                  │
│  - Save to hasil_transformasi.xlsx                          │
└─────────────┬───────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────┐
│                  DOWNLOAD (app.py)                          │
│  - Show download button                                     │
│  - User download hasil_transformasi.xlsx                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Structure

### Output dari process_files()
```json
{
  "principal data": [
    {
      "assignment_id": "...",
      "nama_usaha": "...",
      "alamat": "...",
      ...
    },
    ...
  ],
  "tables": {
    "table_name_1": [
      {"field1": "value1", "field2": "value2", ...},
      ...
    ],
    "table_name_2": [...],
    ...
  },
  "nested": {
    "nested_table_1": [...],
    ...
  }
}
```

---

## Requirements

### File: requirements.txt
```
streamlit==1.28.1
pandas==2.1.3
openpyxl==3.11.0
```

### Installation
```bash
pip install -r requirements.txt
```

### Running Streamlit
```bash
streamlit run app.py
```

---

## Integrasi Points

### 1. Import Statements
```python
# app.py
from cleaning import process_files
from json_to_excel import create_excel
```

### 2. Function Calls

**Di app.py:**
```python
# Call cleaning function
output_clean = temp_path / "data_clean.json"
cleaned_data = process_files(
    template_path,
    answer_dir,
    output_clean
)

# Call excel export function
output_excel = temp_path / "hasil_transformasi.xlsx"
create_excel(cleaned_data, output_excel)
```

### 3. Data Flow
1. app.py → process_files() → cleaned_data (dict)
2. cleaned_data → create_excel() → hasil_transformasi.xlsx

---

## Error Handling

### app.py Error Handling
- Validasi: Template file harus di-upload
- Validasi: Minimal 1 answer JSON file
- Validasi: Maksimal 50 answer JSON files
- Try-except: Catch semua exception saat processing
- Display: Error message dan exception trace

### cleaning.py Error Handling
- FileNotFoundError: Jika tidak ada JSON di input_dir
- ValueError: Jika jumlah file > MAX_FILES
- JSONDecodeError: Jika JSON format tidak valid
- Exception: Catch per file, continue ke file berikutnya

### json_to_excel.py Error Handling
- Validasi: Cell content > 32767 chars (Excel limit)
- Warning: Tampilkan problematic cells di output
- Nested objects validation

---

## Configuration

### app.py
```python
MAX_FILES = 50  # Maksimal file yang bisa di-upload
```

### cleaning.py
```python
TEMPLATE_FILE = "template.json"
INPUT_DIR = Path("data_hasil_parsing")
OUTPUT_FILE = "data_clean.json"
MAX_FILES = 50
```

### json_to_excel.py
```python
INPUT_FILE = "data_clean.json"
OUTPUT_FILE = "data_clean.xlsx"
```

---

## Testing

### Test Case 1: Upload dan Process
1. Start Streamlit: `streamlit run app.py`
2. Upload template.json
3. Upload 1-5 answer JSON files
4. Click "🚀 Proses JSON"
5. Check hasil Excel file
6. Verify: Principal data, main tables, nested tables semua ada

### Test Case 2: Multiple Files
1. Upload template.json
2. Upload 20+ answer JSON files
3. Verify: Semua file terproses dengan benar

### Test Case 3: Large Data
1. Upload template.json
2. Upload answer JSON dengan nested objects dan lists
3. Verify: Data di-flatten dengan benar ke tables

---

## Notes

1. **Temporary Directory**: app.py menggunakan `tempfile.TemporaryDirectory()` untuk proses sehingga tidak meninggalkan file di sistem
2. **Progress Indicator**: Streamlit progress bar menunjukkan status (0% → 20% → 70% → 100%)
3. **Sheet Names**: Maximum 31 characters untuk sheet name (Excel limit)
4. **Cell Content**: Maximum 32767 characters per cell (Excel limit), jika lebih akan di-warn
5. **Data Cleaning**: 
   - String: Trim dan normalize whitespace
   - Number/Boolean: Keep as is
   - Dropdown: Split into value dan label columns
   - Nested: Process separately ke tables

---

## Troubleshooting

### Issue: "Tidak ada JSON di folder"
- Pastikan folder answer berisi file .json
- Periksa nama file extension (.json)

### Issue: "Maksimal 50 file"
- Upload maksimal 50 file sekaligus
- Process beberapa batch jika data lebih dari 50 file

### Issue: "AttributeError: 'PosixPath' object..."
- Pastikan Path object dikonversi ke string jika diperlukan

### Issue: Excel file tidak bisa di-buka
- Check apakah ada cell dengan content > 32.767 karakter
- Cek error message di console Streamlit

---

## Contact & Support
Untuk pertanyaan atau issue, silakan check console output untuk detail error.
