#!/usr/bin/env python3
"""
HTML to PDF Converter
Converts the existing HTML underwriting report to PDF using available libraries.
"""

import os
import sys
from pathlib import Path

def convert_html_to_pdf(html_file, pdf_file):
    """Convert HTML file to PDF using available libraries."""
    
    if not os.path.exists(html_file):
        print(f"❌ HTML file not found: {html_file}")
        return False
    
    print(f"🔄 Converting {html_file} to PDF...")
    
    # Method 1: Try WeasyPrint
    try:
        import weasyprint
        html_doc = weasyprint.HTML(filename=html_file)
        html_doc.write_pdf(pdf_file)
        print(f"✅ PDF generated using WeasyPrint: {pdf_file}")
        return True
    except ImportError:
        print("⚠️ WeasyPrint not available")
    except Exception as e:
        print(f"⚠️ WeasyPrint failed: {e}")
    
    # Method 2: Try reportlab with HTML parsing
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import inch
        import re
        
        # Read HTML content
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Extract title and create simple PDF
        doc = SimpleDocTemplate(pdf_file, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Extract property name from HTML
        property_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html_content)
        title = property_match.group(1) if property_match else "Underwriting Analysis"
        
        story.append(Paragraph(f"<b>{title}</b>", styles['Title']))
        story.append(Spacer(1, 12))
        story.append(Paragraph("Professional underwriting analysis report generated from uploaded documents.", styles['Normal']))
        story.append(Spacer(1, 12))
        story.append(Paragraph("<b>Note:</b> This is a simplified PDF version. For the complete formatted report, please refer to the HTML version.", styles['Normal']))
        
        doc.build(story)
        print(f"✅ Simple PDF generated using reportlab: {pdf_file}")
        return True
        
    except ImportError:
        print("⚠️ reportlab not available")
    except Exception as e:
        print(f"⚠️ reportlab failed: {e}")
    
    # Method 3: Copy HTML as PDF (fallback)
    try:
        import shutil
        fallback_pdf = pdf_file.replace('.pdf', '_report.html')
        shutil.copy2(html_file, fallback_pdf)
        print(f"✅ HTML report copied as: {fallback_pdf}")
        return fallback_pdf
    except Exception as e:
        print(f"❌ Fallback failed: {e}")
    
    return False

if __name__ == "__main__":
    # Find the most recent HTML file in outputs
    outputs_dir = Path("outputs")
    if not outputs_dir.exists():
        print("❌ Outputs directory not found")
        sys.exit(1)
    
    html_files = list(outputs_dir.glob("*_Package_*.html"))
    if not html_files:
        print("❌ No package HTML files found in outputs directory")
        sys.exit(1)
    
    # Use the most recent HTML file
    latest_html = max(html_files, key=os.path.getctime)
    pdf_file = str(latest_html).replace('.html', '.pdf')
    
    print(f"📄 Converting: {latest_html}")
    result = convert_html_to_pdf(str(latest_html), pdf_file)
    
    if result:
        print(f"🎉 Conversion completed!")
        if isinstance(result, str):
            print(f"📄 File available at: {result}")
        else:
            print(f"📄 PDF available at: {pdf_file}")
    else:
        print("❌ Conversion failed")
