import streamlit as st
from datetime import datetime
from fpdf import FPDF


class PDF(FPDF):
    def header(self):
        self.set_fill_color(31, 119, 180)
        self.rect(0, 0, 210, 35, 'F')
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 22)
        self.cell(0, 15, "LOCAL RAG SYSTEM", ln=True, align='C')
        self.set_font("Helvetica", "I", 9)
        self.cell(0, 5, "ANONYMIZED TECHNICAL ANALYSIS REPORT", ln=True, align='C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()} | Confidential | Generated on {datetime.now().strftime('%Y-%m-%d')}", align='C')

    def draw_watermark(self):
        self.set_font("Helvetica", "B", 50)
        self.set_text_color(240, 240, 240)
        with self.rotation(45, 105, 148):
            self.text(40, 190, "SECURE REPORT")


def export_chat_to_pdf(chat_id: str) -> bytes:
    chat = st.session_state.chats[chat_id]
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    pdf.draw_watermark()
    w = pdf.w - 2 * pdf.l_margin

    pdf.set_text_color(40, 40, 40)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, f"CHAT ID: {chat_id[:8].upper()}", ln=True)
    pdf.cell(0, 8, f"SUBJECT: {chat['name'].upper()}", ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, f"EXCHANGE COUNT: {len(chat['messages'])} messages", ln=True)
    pdf.ln(10)

    for msg in chat['messages']:
        role = msg['role'].upper()
        pdf.set_fill_color(245, 245, 245)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(31, 119, 180)
        pdf.cell(0, 8, f" [{role}]", ln=True, fill=True)
        pdf.ln(2)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "", 10)
        clean_text = msg['content'].replace("**", "").replace("*", "").replace("`", "")
        clean_text = clean_text.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(w, 6, clean_text)

        if msg.get("metrics"):
            pdf.ln(3)
            pdf.set_fill_color(250, 253, 255)
            pdf.set_draw_color(200, 220, 240)
            pdf.set_font("Helvetica", "I", 8)
            pdf.set_text_color(80, 100, 120)
            metrics_txt = f"EVALUATION METRICS: {msg['metrics']}".replace("**", "").encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(w, 5, metrics_txt, border=1, fill=True)

        citations = msg.get("citations", [])
        if citations:
            pdf.ln(3)
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(100, 100, 100)
            pdf.cell(0, 6, "DATA SOURCES:", ln=True)
            pdf.set_font("Helvetica", "", 8)
            for cite in citations:
                pdf.cell(5)
                pdf.cell(0, 4, f"- {cite['source'].encode('latin-1', 'replace').decode('latin-1')}", ln=True)

        pdf.ln(10)
        pdf.set_draw_color(230, 230, 230)
        pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
        pdf.ln(5)

    return bytes(pdf.output())
