# agents/tools/pdf_exporter.py

from fpdf import FPDF

def generate_pdf(text: str, output_path: str = "report.pdf"):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    for line in text.split("\n"):
        pdf.multi_cell(0, 8, line)

    pdf.output(output_path)

    return {
        "status": "success",
        "file": output_path
    }
