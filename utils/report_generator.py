from fpdf import FPDF

class PDFReport(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 15)
        self.cell(0, 10, 'Sales Call Coaching Report', 0, 1, 'C')
        self.ln(5)
        
    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generate_pdf_report(analysis, metrics):
    """
    Generates a PDF report bytes object.
    """
    pdf = PDFReport(orientation='P', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_margins(10, 10, 10)
    pdf.add_page()
    
    # Effective width for A4 (210mm) with 10mm margins on both sides = 190mm
    eff_width = 190

    def clean_text(text):
        """Sanitizes text for standard PDF fonts (Latin-1)."""
        if not text: return ""
        # Replace common incompatible characters
        text = text.replace("’", "'").replace("“", '"').replace("”", '"').replace("–", "-")
        # Encode to latin-1, replacing errors with '?'
        return text.encode('latin-1', 'replace').decode('latin-1')

    # Fonts
    # Using standard fonts to avoid dependency on font files
    pdf.set_font("Helvetica", size=12)
    
    # 1. Executive Summary
    pdf.set_font("Helvetica", 'B', 14)
    # Reset X before headers/blocks to be safe
    pdf.set_x(10)
    pdf.cell(0, 10, "Executive Summary", 0, 1)
    
    pdf.set_font("Helvetica", size=11)
    pdf.set_x(10)
    # Multi_cell for text wrapping
    pdf.multi_cell(eff_width, 7, clean_text(analysis.get('summary', 'No summary available.')))
    pdf.ln(5)
    
    # 2. Metrics
    pdf.set_font("Helvetica", 'B', 14)
    pdf.set_x(10)
    pdf.cell(0, 10, "Key Metrics", 0, 1)
    pdf.set_font("Helvetica", size=11)
    pdf.set_x(10)
    
    metric_text = f"Sentiment Score: {analysis.get('sentiment_score', 'N/A')}/100\n" \
                  f"Word Count: {metrics.get('word_count', 'N/A')}\n" \
                  f"Estimated Duration: {metrics.get('estimated_duration_mins', 'N/A')} mins"
    pdf.multi_cell(eff_width, 7, clean_text(metric_text))
    pdf.ln(5)
    
    # 3. What Went Well
    pdf.set_font("Helvetica", 'B', 14)
    pdf.set_text_color(0, 150, 0) # Greenish
    pdf.set_x(10)
    pdf.cell(0, 10, "What Went Well", 0, 1)
    pdf.set_text_color(0, 0, 0) # Reset
    pdf.set_font("Helvetica", size=11)
    
    for item in analysis.get('strengths', []):
        pdf.set_x(10)
        pdf.multi_cell(eff_width, 7, f"- {clean_text(item)}")
    pdf.ln(5)

    # 4. Areas for Improvement
    pdf.set_font("Helvetica", 'B', 14)
    pdf.set_text_color(200, 100, 0) # Orangey
    pdf.set_x(10)
    pdf.cell(0, 10, "Areas for Improvement", 0, 1)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", size=11)
    
    for item in analysis.get('improvements', []):
        pdf.set_x(10)
        pdf.multi_cell(eff_width, 7, f"- {clean_text(item)}")
    pdf.ln(5)

    # 5. Coaching Tips
    pdf.set_font("Helvetica", 'B', 14)
    pdf.set_text_color(0, 0, 150) # Blueish
    pdf.set_x(10)
    pdf.cell(0, 10, "Coaching Tips", 0, 1)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", size=11)
    
    for tip in analysis.get('coaching_tips', []):
        pdf.set_x(10)
        pdf.multi_cell(eff_width, 7, f"- {clean_text(tip)}")
    pdf.ln(5)
    
    return bytes(pdf.output())
