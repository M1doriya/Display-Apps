import streamlit as st
from tensorlake.documentai import (
    DocumentAI,
    ParsingOptions,
    EnrichmentOptions,
    ParseStatus,
    ChunkingStrategy,
    TableOutputMode,
    TableParsingFormat,
    OcrPipelineProvider,
)

import json
from bs4 import BeautifulSoup
from tabulate import tabulate
import tempfile
import pandas as pd
import httpx
import os

# ===================================================
# 🔑 CONFIG — API Key from Environment Variable
# ===================================================

API_KEY = os.environ.get("TENSORLAKE_API_KEY")



# ===================================================
# 🔧 FIXED — Correct Tensorlake v2 Upload Function
# ===================================================

def upload_file_v2(path):
    """
    Uploads a file to Tensorlake using the correct v2 API:
    PUT /documents/v2/files
    """
    url = "https://api.tensorlake.ai/documents/v2/files"

    with open(path, "rb") as f:
        files = {"file_bytes": ("file.pdf", f, "application/pdf")}
        data = {"labels": json.dumps({"source": "streamlit_app"})}

        response = httpx.put(
            url,
            headers={"Authorization": f"Bearer {API_KEY}"},
            files=files,
            data=data,
            timeout=30
        )

    if response.status_code != 200:
        raise Exception(f"Upload failed {response.status_code}: {response.text}")

    return response.json()["file_id"]



# ===================================================
# Helper Functions
# ===================================================

def clean_number(value):
    try:
        return int(value.replace(",", ""))
    except Exception:
        return value

def fix_duplicate_headers(headers):
    seen = {}
    fixed = []
    for h in headers:
        key = h if h.strip() else "col"
        if key not in seen:
            seen[key] = 1
            fixed.append(key)
        else:
            seen[key] += 1
            fixed.append(f"{key}_{seen[key]}")
    return fixed

def html_table_to_matrix(table):
    rows = table.find_all("tr")
    return [[cell.get_text(strip=True) for cell in row.find_all(["td", "th"])] for row in rows]

def html_table_to_objects(table):
    matrix = html_table_to_matrix(table)
    if not matrix or len(matrix) < 2:
        return []

    header = matrix[0]
    objects = []

    for row in matrix[1:]:
        entry = {}
        for h, v in zip(header, row):
            h_low = h.lower().strip()

            if h_low in ["2024", "year_2024"]:
                entry["year_2024"] = clean_number(v)
            elif h_low in ["2023", "as restated 2023", "year_2023"]:
                entry["year_2023"] = clean_number(v)
            elif h_low == "note":
                entry["note"] = clean_number(v) if v else None
            else:
                entry["name"] = v

        objects.append(entry)

    return objects



# ===================================================
# Streamlit Session State
# ===================================================

if "results" not in st.session_state:
    st.session_state["results"] = None



# ===================================================
# Rendering Function
# ===================================================

def render_results(results):
    if not results:
        return

    for page in results["pages"]:
        st.header(f"📄 Page {page['page_number']}")

        st.subheader("📝 Extracted Text")
        st.markdown(page["text_display"])

        for t_index, table in enumerate(page["tables"], start=1):
            st.subheader(f"📊 Table {t_index}")
            df = pd.DataFrame(table["rows"], columns=table["headers"])
            st.table(df)

    # Downloads
    st.success("✅ Extraction complete!")

    st.download_button(
        "📥 Download Text (No Tables)",
        results["full_text_output"].encode("utf-8"),
        file_name="document.txt",
        mime="text/plain",
    )

    st.download_button(
        "📥 Download Text + Tables",
        results["full_text_with_tables"].encode("utf-8"),
        file_name="document_with_tables.txt",
        mime="text/plain",
    )

    st.download_button(
        "📥 Download Tables JSON",
        json.dumps(results["all_tables_json"], indent=4).encode("utf-8"),
        file_name="tables.json",
        mime="application/json",
    )



# ===================================================
# Streamlit UI + Detailed Descriptions
# ===================================================

# ===================================================
# Streamlit UI With Inline Descriptions
# ===================================================

st.set_page_config(page_title="PDF Parser", layout="wide")
st.title("📄 PDF Extractor (Tensorlake DocumentAI)")

st.header("⚙️ Parsing Configuration")


# ============================
# OCR Model (with inline help)
# ============================
st.markdown("### OCR Model")
st.write("""
- **model01** → Balanced OCR, good general accuracy  
- **model02** → ⭐ Recommended. Best accuracy for tables & financial documents  
- **model03** → Fastest OCR, ideal for large batches  
""")

ocr_choice = st.radio(
    "Select OCR Model:",
    ["model01", "model02", "model03"],
    index=1  # default: model02
)

ocr_map = {
    "model01": OcrPipelineProvider.TENSORLAKE01,
    "model02": OcrPipelineProvider.TENSORLAKE02,
    "model03": OcrPipelineProvider.TENSORLAKE03,
}


# ============================
# Table Output Mode
# ============================
st.markdown("### Table Output Mode")
st.write("""
- **MARKDOWN** → Clean and readable (recommended)  
- **HTML** → Full HTML table  
- **TSV** → Export-friendly  
""")

table_output_choice = st.selectbox(
    "Select Table Output Mode:",
    list(TableOutputMode),
    index=list(TableOutputMode).index(TableOutputMode.MARKDOWN)
)


# ============================
# Table Parsing Format (Corrected)
# ============================
st.markdown("### Table Parsing Format")
st.write("""
- **TSR** → Tensorlake Structured Recognition (best for most PDFs)  
- **VLM** → Vision-Language Model parsing (good for complex layouts)  
""")

valid_parsing_modes = [
    TableParsingFormat.TSR,
    TableParsingFormat.VLM
]

table_parsing_choice = st.selectbox(
    "Select Table Parsing Format:",
    valid_parsing_modes,
    index=0  # default: TSR
)


# ============================
# Chunking Strategy
# ============================
st.markdown("### Chunking Strategy")
st.write("""
- **PAGE** → Recommended. Processes each page independently  
- **SLIDING_WINDOW** → Better for dense paragraphs  
- **MULTICOLUMN** → For magazines, 2-column documents  
""")

chunking_choice = st.selectbox(
    "Select Chunking Strategy:",
    list(ChunkingStrategy),
    index=list(ChunkingStrategy).index(ChunkingStrategy.PAGE)
)


# ============================
# Advanced Options (Inline Help)
# ============================

st.markdown("### Advanced Options")
st.write("""
- **Cross-page Header Detection** → Detect table headers across pages  
- **Signature Detection** → Extract signature blocks  
- **Remove Strikethrough Lines** → Ignores crossed-out text  
- **Enable Skew Detection** → Auto-straighten rotated scans (**recommended on**)  
- **Disable Layout Detection** → Turns off layout detection (only for simple PDFs)  
""")

cross_page_headers = st.checkbox("Cross-page Header Detection", value=False)
signature_detection = st.checkbox("Signature Detection", value=False)
remove_strike = st.checkbox("Remove Strikethrough Lines", value=False)
skew_detection = st.checkbox("Enable Skew Detection", value=True)  # Default ON
disable_layout_detection = st.checkbox("Disable Layout Detection", value=False)

st.divider()



# ===================================================
# PDF Upload
# ===================================================

uploaded_pdf = st.file_uploader("Upload PDF File", type=["pdf"])
run_button = st.button("🚀 Start Parsing")

if st.session_state["results"] and not run_button:
    render_results(st.session_state["results"])



# ===================================================
# Main Logic — Upload + Parse
# ===================================================

if run_button:

    if not API_KEY:
        st.error("❌ TENSORLAKE_API_KEY environment variable is not set. Please configure it in Railway.")
        st.stop()

    if not uploaded_pdf:
        st.error("Please upload a PDF file.")
        st.stop()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_pdf.read())
        temp_pdf_path = tmp.name

    try:
        with st.spinner("📤 Uploading file..."):
            file_id = upload_file_v2(temp_pdf_path)

        doc_ai = DocumentAI(api_key=API_KEY)

        parsing_options = ParsingOptions(
            chunking_strategy=chunking_choice,
            table_output_mode=table_output_choice,
            table_parsing_format=table_parsing_choice,
            ocr_model=ocr_map[ocr_choice],
            cross_page_header_detection=cross_page_headers,
            signature_detection=signature_detection,
            remove_strikethrough_lines=remove_strike,
            skew_detection=skew_detection,
            disable_layout_detection=disable_layout_detection,
        )

        enrichment_options = EnrichmentOptions(
            figure_summarization=False,
            table_summarization=False,
        )

        with st.spinner("🔍 Parsing PDF..."):
            result = doc_ai.parse_and_wait(
                file_id=file_id,
                parsing_options=parsing_options,
                enrichment_options=enrichment_options,
            )

        if result.status != ParseStatus.SUCCESSFUL:
            st.error(f"❌ Parsing failed: {result.status}")
            st.stop()

        # ===================================================
        # Build result structure
        # ===================================================

        full_text_output = ""
        full_text_with_tables = ""
        all_tables_json = {"tables": []}
        pages = []

        for i, chunk in enumerate(result.chunks, start=1):
            raw_markdown = chunk.content
            soup = BeautifulSoup(raw_markdown, "html.parser")
            tables = soup.find_all("table")

            for t in tables:
                t.extract()

            text_plain = soup.get_text("\n", strip=True)

            full_text_output += f"\n\n===== PAGE {i} =====\n\n{text_plain}\n\n"
            full_text_with_tables += f"\n\n===== PAGE {i} =====\n\n{text_plain}\n\n"

            page_tables = []

            for t_index, table in enumerate(tables, start=1):
                matrix = html_table_to_matrix(table)
                if not matrix or len(matrix) < 2:
                    continue

                headers = fix_duplicate_headers(matrix[0])
                rows = matrix[1:]

                readable = tabulate(rows, headers=headers, tablefmt="grid")
                full_text_with_tables += readable + "\n\n"

                all_tables_json["tables"].append({
                    "page": i,
                    "table_index": t_index,
                    "rows": html_table_to_objects(table),
                })

                page_tables.append({"headers": headers, "rows": rows})

            pages.append({
                "page_number": i,
                "text_display": raw_markdown,
                "text_plain": text_plain,
                "tables": page_tables,
            })

        st.session_state["results"] = {
            "pages": pages,
            "full_text_output": full_text_output,
            "full_text_with_tables": full_text_with_tables,
            "all_tables_json": all_tables_json,
        }

        render_results(st.session_state["results"])

    finally:
        if os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)
