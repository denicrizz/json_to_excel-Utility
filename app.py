import streamlit as st
import json
import tempfile
from pathlib import Path

from cleaning import process_files
from json_to_excel import create_excel


# ============================================================
# KONFIGURASI
# ============================================================

MAX_FILES = 50


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="BPS Kota Kediri JSON → Excel Utility",
    page_icon="📊",
    layout="centered",
)


# ============================================================
# HEADER
# ============================================================

st.title("📊 BPS Kota Kediri JSON to Excel Utility")

st.write(
    """
    Sistem ini dibuat untuk menkonversi data dari JSON
    dan menghasilkan file Excel yang siap untuk dipakai.
    """
)


# ============================================================
# KONFIGURASI PATH TEMPLATE
# ============================================================

template_path_file = Path("template.json")


# ============================================================
# UPLOAD ANSWER
# ============================================================

st.subheader("Upload File")

answer_files = st.file_uploader(
    f"Pilih maksimal {MAX_FILES} file",
    type=["json"],
    accept_multiple_files=True
)


# ============================================================
# INFORMASI FILE
# ============================================================

if answer_files:

    st.info(
        f"{len(answer_files)} file answer.JSON siap diproses."
    )


# ============================================================
# BUTTON
# ============================================================

if st.button(
    "🚀 Proses",
    type="primary",
    use_container_width=True
):

    if len(answer_files) > MAX_FILES:

        st.error(
            f"Maksimal {MAX_FILES} file. "
            f"Kamu memilih {len(answer_files)} file."
        )

        st.stop()

    if not answer_files:

        st.error(
            "Silakan upload minimal 1 answer JSON."
        )

        st.stop()


    # ========================================================
    # TEMP DIRECTORY
    # ========================================================

    with tempfile.TemporaryDirectory() as temp_dir:

        temp_path = Path(
            temp_dir
        )


        # ====================================================
        # SIMPAN ANSWER
        # ====================================================

        answer_dir = (
            temp_path /
            "answers"
        )

        answer_dir.mkdir()


        for uploaded_file in answer_files:

            file_path = (
                answer_dir /
                uploaded_file.name
            )

            file_path.write_bytes(
                uploaded_file.getvalue()
            )


        # ====================================================
        # PROGRESS
        # ====================================================

        progress = st.progress(
            0
        )

        status = st.empty()


        try:

            # =================================================
            # CLEANING
            # =================================================

            status.write(
                "🔄 Membaca template dan answer JSON..."
            )

            progress.progress(
                20
            )

            # Tentukan path untuk file output cleaning
            output_clean = (
                temp_path /
                "data_clean.json"
            )

            cleaned_data = process_files(
                template_path_file,
                answer_dir,
                output_clean
            )


            # =================================================
            # EXCEL
            # =================================================

            status.write(
                "📊 Membuat file Excel..."
            )

            progress.progress(
                70
            )


            output_excel = (
                temp_path /
                "hasil_konversi.xlsx"
            )


            create_excel(
                cleaned_data,
                output_excel
            )


            # =================================================
            # SELESAI
            # =================================================

            progress.progress(
                100
            )

            status.success(
                "✅ Proses selesai!"
            )


            # =================================================
            # DOWNLOAD
            # =================================================

            with open(
                output_excel,
                "rb"
            ) as f:

                excel_bytes = f.read()


            st.download_button(
                label="⬇️ Download File Excel",
                data=excel_bytes,
                file_name="hasil_transformasi.xlsx",
                mime=(
                    "application/"
                    "vnd.openxmlformats-officedocument"
                    ".spreadsheetml.sheet"
                ),
                use_container_width=True
            )


        except Exception as e:

            st.error(
                "❌ Terjadi error saat memproses data."
            )

            st.exception(
                e
            )