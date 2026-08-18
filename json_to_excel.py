import json
import re
from pathlib import Path

import pandas as pd


# ============================================================
# KONFIGURASI
# ============================================================

INPUT_FILE = "data_clean.json"
OUTPUT_FILE = "data_clean.xlsx"


# ============================================================
# LOAD DATA
# ============================================================

def load_data(input_file):
    with open(
        input_file,
        "r",
        encoding="utf-8"
    ) as f:
        return json.load(f)


# ============================================================
# NAMA SHEET
# ============================================================

def clean_sheet_name(name):

    name = str(name)

    # Karakter yang tidak boleh digunakan Excel
    name = re.sub(
        r'[:\\/?*\[\]]',
        "_",
        name
    )

    # Maksimal 31 karakter
    name = name[:31]

    if not name:
        name = "Sheet"

    return name


# ============================================================
# HANDLE DUPLICATE SHEET NAME
# ============================================================

def unique_sheet_name(
    name,
    used_names
):

    name = clean_sheet_name(
        name
    )

    original = name
    counter = 2

    while name in used_names:

        suffix = f"_{counter}"

        name = (
            original[:31 - len(suffix)]
            + suffix
        )

        counter += 1

    used_names.add(name)

    return name


# ============================================================
# CEK VALUE
# ============================================================

def make_dataframe(rows):

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    # Kolom yang tidak ada pada suatu JSON
    # otomatis menjadi kosong
    df = df.fillna("")

    return df


# ============================================================
# CEK DATA YANG TERLALU PANJANG
# ============================================================

def check_long_cells(
    df,
    table_name
):

    problems = []

    for column in df.columns:

        for index, value in df[column].items():

            if value is None:
                continue

            # Dictionary/list seharusnya tidak sampai sini
            if isinstance(
                value,
                (dict, list)
            ):
                problems.append({
                    "table": table_name,
                    "row": index,
                    "column": column,
                    "type": type(value).__name__,
                    "length": "NESTED OBJECT"
                })

                continue

            text = str(value)

            if len(text) > 32767:

                problems.append({
                    "table": table_name,
                    "row": index,
                    "column": column,
                    "type": type(value).__name__,
                    "length": len(text)
                })

    return problems


# ============================================================
# EXPORT EXCEL
# ============================================================

def create_excel(
    cleaned_data,
    output_file
):

    used_sheet_names = set()

    total_tables = 0

    warnings = []


    with pd.ExcelWriter(
        output_file,
        engine="openpyxl"
    ) as writer:

        # ====================================================
        # PRINCIPAL DATA
        # ====================================================

        principal = cleaned_data.get(
            "principal data",
            []
        )

        df_principal = make_dataframe(
            principal
        )

        if not df_principal.empty:

            problems = check_long_cells(
                df_principal,
                "principal data"
            )

            warnings.extend(
                problems
            )

            sheet_name = unique_sheet_name(
                "principal data",
                used_sheet_names
            )

            df_principal.to_excel(
                writer,
                sheet_name=sheet_name,
                index=False
            )

            total_tables += 1


        # ====================================================
        # TABLE NORMAL
        # ====================================================

        tables = cleaned_data.get(
            "tables",
            {}
        )

        for table_name, rows in tables.items():

            df = make_dataframe(
                rows
            )

            if df.empty:
                continue


            problems = check_long_cells(
                df,
                table_name
            )

            warnings.extend(
                problems
            )


            sheet_name = unique_sheet_name(
                table_name,
                used_sheet_names
            )


            df.to_excel(
                writer,
                sheet_name=sheet_name,
                index=False
            )

            total_tables += 1


        # ====================================================
        # TABLE NESTED
        # ====================================================

        nested_tables = cleaned_data.get(
            "nested",
            {}
        )

        for table_name, rows in nested_tables.items():

            df = make_dataframe(
                rows
            )

            if df.empty:
                continue


            problems = check_long_cells(
                df,
                table_name
            )

            warnings.extend(
                problems
            )


            sheet_name = unique_sheet_name(
                table_name,
                used_sheet_names
            )


            df.to_excel(
                writer,
                sheet_name=sheet_name,
                index=False
            )

            total_tables += 1


    # ========================================================
    # INFORMASI
    # ========================================================

    print("=" * 70)
    print("EXCEL BERHASIL")
    print("=" * 70)

    print(
        f"Jumlah tabel : {total_tables}"
    )

    print(
        f"Output       : {output_file}"
    )


    if warnings:

        print()
        print(
            "PERINGATAN DATA:"
        )

        for item in warnings:

            print(
                f"- Table={item['table']} | "
                f"Kolom={item['column']} | "
                f"Baris={item['row']} | "
                f"Panjang={item['length']}"
            )

    else:

        print(
            "Tidak ada cell > 32.767 karakter."
        )

    print("=" * 70)


# ============================================================
# MAIN
# ============================================================

def main():

    data = load_data(
        INPUT_FILE
    )

    create_excel(
        data,
        OUTPUT_FILE
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main()