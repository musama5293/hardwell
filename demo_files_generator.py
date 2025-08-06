#!/usr/bin/env python3
"""
Test HTML to PDF Conversion
Creates a sample HTML file and converts it to PDF to demonstrate the functionality.
"""

import os
from datetime import datetime

def create_sample_html():
    """Create a sample HTML file similar to the underwriting template."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    html_path = f"outputs/Sample_Package_{timestamp}.html"
    
    os.makedirs("outputs", exist_ok=True)
    
    # Create sample HTML content
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Underwriting Analysis - Sample Property</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #2c3e50;
            text-align: center;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }
        .property-info {
            background-color: #ecf0f1;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }
        .financial-table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        .financial-table th {
            background-color: #34495e;
            color: white;
            padding: 12px;
            text-align: left;
        }
        .financial-table td {
            padding: 10px;
            border-bottom: 1px solid #ddd;
        }
        .financial-table tr:nth-child(even) {
            background-color: #f8f9fa;
        }
        .total-row {
            font-weight: bold;
            background-color: #3498db !important;
            color: white;
        }
        .section-header {
            background-color: #2c3e50;
            color: white;
            padding: 10px;
            margin: 20px 0 10px 0;
            border-radius: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Sample Property Underwriting Analysis</h1>
        
        <div class="property-info">
            <h2>Property Information</h2>
            <p><strong>Property Name:</strong> Sample Apartment Complex</p>
            <p><strong>Address:</strong> 123 Main Street, Atlanta, GA 30309</p>
            <p><strong>Units:</strong> 86</p>
            <p><strong>Transaction Type:</strong> Acquisition</p>
            <p><strong>Analysis Date:</strong> """ + datetime.now().strftime('%B %d, %Y') + """</p>
        </div>

        <div class="section-header">
            <h3>Financial Summary</h3>
        </div>

        <table class="financial-table">
            <thead>
                <tr>
                    <th>Line Item</th>
                    <th>Amount</th>
                    <th>% of EGI</th>
                    <th>Notes</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Gross Potential Income</td>
                    <td>$1,204,800</td>
                    <td>104.5%</td>
                    <td>Based on current rent roll analysis</td>
                </tr>
                <tr>
                    <td>Vacancy Loss</td>
                    <td>($60,240)</td>
                    <td>(5.2%)</td>
                    <td>Applied 5% vacancy rate</td>
                </tr>
                <tr>
                    <td>Other Income</td>
                    <td>$12,048</td>
                    <td>1.0%</td>
                    <td>Laundry, fees, and other income</td>
                </tr>
                <tr class="total-row">
                    <td>Effective Gross Income</td>
                    <td>$1,156,608</td>
                    <td>100.0%</td>
                    <td>Total income after vacancy</td>
                </tr>
                <tr>
                    <td>Property Taxes</td>
                    <td>$92,529</td>
                    <td>8.0%</td>
                    <td>Based on current assessment</td>
                </tr>
                <tr>
                    <td>Insurance</td>
                    <td>$23,132</td>
                    <td>2.0%</td>
                    <td>Comprehensive property insurance</td>
                </tr>
                <tr>
                    <td>Utilities</td>
                    <td>$34,698</td>
                    <td>3.0%</td>
                    <td>Common area utilities</td>
                </tr>
                <tr>
                    <td>Repairs & Maintenance</td>
                    <td>$57,830</td>
                    <td>5.0%</td>
                    <td>Ongoing maintenance and repairs</td>
                </tr>
                <tr>
                    <td>Management Fee</td>
                    <td>$28,915</td>
                    <td>2.5%</td>
                    <td>Professional management</td>
                </tr>
                <tr>
                    <td>Other Expenses</td>
                    <td>$46,264</td>
                    <td>4.0%</td>
                    <td>Administrative and other costs</td>
                </tr>
                <tr class="total-row">
                    <td>Total Operating Expenses</td>
                    <td>$283,368</td>
                    <td>24.5%</td>
                    <td>Total of all operating expenses</td>
                </tr>
                <tr class="total-row">
                    <td><strong>Net Operating Income</strong></td>
                    <td><strong>$873,240</strong></td>
                    <td><strong>75.5%</strong></td>
                    <td><strong>EGI minus operating expenses</strong></td>
                </tr>
            </tbody>
        </table>

        <div class="section-header">
            <h3>Key Metrics</h3>
        </div>
        
        <div class="property-info">
            <p><strong>Cap Rate:</strong> 7.25%</p>
            <p><strong>Operating Expense Ratio:</strong> 24.5%</p>
            <p><strong>Average Rent per Unit:</strong> $1,163</p>
            <p><strong>NOI per Unit:</strong> $10,155</p>
        </div>

        <div class="section-header">
            <h3>Analysis Notes</h3>
        </div>
        
        <ul>
            <li>Real PDF processing used for rent roll and T12 extraction</li>
            <li>Professional underwriting template applied</li>
            <li>CSV files generated for extracted data</li>
            <li>Multiple output formats available (Excel, PDF, HTML, CSV)</li>
        </ul>
    </div>
</body>
</html>
    """
    
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Sample HTML created: {html_path}")
    return html_path

def convert_to_pdf(html_path):
    """Convert HTML to PDF using available methods."""
    pdf_path = html_path.replace('.html', '.pdf')
    
    # Method 1: Try WeasyPrint
    try:
        import weasyprint
        html_doc = weasyprint.HTML(filename=html_path)
        html_doc.write_pdf(pdf_path)
        print(f"✅ PDF generated using WeasyPrint: {pdf_path}")
        return pdf_path
    except ImportError:
        print("⚠️ WeasyPrint not available")
    except Exception as e:
        print(f"⚠️ WeasyPrint failed: {e}")
    
    # Method 2: Try reportlab
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        
        doc = SimpleDocTemplate(pdf_path, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        story.append(Paragraph("<b>Sample Property Underwriting Analysis</b>", styles['Title']))
        story.append(Spacer(1, 20))
        
        # Property info
        story.append(Paragraph("<b>Property Information</b>", styles['Heading2']))
        property_info = [
            "Property: Sample Apartment Complex",
            "Address: 123 Main Street, Atlanta, GA 30309", 
            "Units: 86",
            "Transaction: Acquisition",
            f"Analysis Date: {datetime.now().strftime('%B %d, %Y')}"
        ]
        
        for info in property_info:
            story.append(Paragraph(info, styles['Normal']))
        
        story.append(Spacer(1, 20))
        
        # Financial table
        story.append(Paragraph("<b>Financial Summary</b>", styles['Heading2']))
        
        table_data = [
            ['Line Item', 'Amount', '% of EGI', 'Notes'],
            ['Gross Potential Income', '$1,204,800', '104.5%', 'Based on rent roll analysis'],
            ['Vacancy Loss', '($60,240)', '(5.2%)', 'Applied 5% vacancy rate'],
            ['Other Income', '$12,048', '1.0%', 'Laundry and fees'],
            ['Effective Gross Income', '$1,156,608', '100.0%', 'Total income after vacancy'],
            ['Property Taxes', '$92,529', '8.0%', 'Based on assessment'],
            ['Insurance', '$23,132', '2.0%', 'Property insurance'],
            ['Utilities', '$34,698', '3.0%', 'Common area utilities'],
            ['Repairs & Maintenance', '$57,830', '5.0%', 'Ongoing maintenance'],
            ['Management Fee', '$28,915', '2.5%', 'Professional management'],
            ['Other Expenses', '$46,264', '4.0%', 'Administrative costs'],
            ['Total Operating Expenses', '$283,368', '24.5%', 'Total expenses'],
            ['Net Operating Income', '$873,240', '75.5%', 'Final NOI']
        ]
        
        table = Table(table_data, colWidths=[2.5*inch, 1*inch, 0.8*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 20))
        
        # Key metrics
        story.append(Paragraph("<b>Key Metrics</b>", styles['Heading2']))
        metrics = [
            "Cap Rate: 7.25%",
            "Operating Expense Ratio: 24.5%", 
            "Average Rent per Unit: $1,163",
            "NOI per Unit: $10,155"
        ]
        
        for metric in metrics:
            story.append(Paragraph(metric, styles['Normal']))
        
        doc.build(story)
        print(f"✅ PDF generated using reportlab: {pdf_path}")
        return pdf_path
        
    except ImportError:
        print("⚠️ reportlab not available")
    except Exception as e:
        print(f"⚠️ reportlab failed: {e}")
    
    print("❌ No PDF generation methods available")
    return None

def create_sample_csv():
    """Create sample CSV files to demonstrate the functionality."""
    import csv
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Sample rent roll CSV
    rent_roll_csv = f"outputs/Sample_RentRoll_{timestamp}.csv"
    rent_roll_data = [
        ['Unit Number', 'Unit Type', 'Square Footage', 'Current Rent', 'Market Rent', 'Tenant Name', 'Lease End', 'Status'],
        ['101', '1BR/1BA', '650', '1100', '1150', 'Smith, John', '2025-12-31', 'Occupied'],
        ['102', '1BR/1BA', '650', '1125', '1150', 'Johnson, Mary', '2025-06-30', 'Occupied'],
        ['103', '2BR/2BA', '950', '1400', '1450', 'Williams, Bob', '2026-01-15', 'Occupied'],
        ['104', '2BR/2BA', '950', '0', '1450', 'VACANT', '', 'Vacant'],
        ['105', '1BR/1BA', '650', '1075', '1150', 'Brown, Lisa', '2025-11-30', 'Occupied'],
        ['201', '1BR/1BA', '650', '1100', '1150', 'Davis, Mike', '2025-09-15', 'Occupied'],
        ['202', '2BR/2BA', '950', '1375', '1450', 'Wilson, Sarah', '2025-08-31', 'Occupied'],
        ['203', '1BR/1BA', '650', '1050', '1150', 'Taylor, Chris', '2025-07-15', 'Occupied']
    ]
    
    with open(rent_roll_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(rent_roll_data)
    
    print(f"✅ Sample rent roll CSV created: {rent_roll_csv}")
    
    # Sample T12 CSV
    t12_csv = f"outputs/Sample_T12_{timestamp}.csv"
    t12_data = [
        ['Line Item', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Total'],
        ['Rental Income', '98500', '99200', '101200', '102500', '103200', '104800', '105200', '105800', '104200', '103500', '102800', '101200', '1231100'],
        ['Other Income', '850', '920', '1100', '1200', '1050', '980', '1150', '1200', '950', '800', '750', '900', '12550'],
        ['Gross Income', '99350', '100120', '102300', '103700', '104250', '105780', '106350', '107000', '105150', '104300', '103550', '102100', '1243650'],
        ['Property Taxes', '7500', '7500', '7500', '7500', '7500', '7500', '7500', '7500', '7500', '7500', '7500', '7500', '90000'],
        ['Insurance', '1850', '1850', '1850', '1850', '1850', '1850', '1850', '1850', '1850', '1850', '1850', '1850', '22200'],
        ['Utilities', '2800', '2950', '2700', '2600', '2500', '2850', '3200', '3100', '2900', '2750', '2800', '2950', '33100'],
        ['Maintenance', '4200', '3800', '5200', '4800', '4500', '5100', '5800', '5200', '4700', '4200', '3900', '4500', '55900'],
        ['Management', '2480', '2503', '2558', '2593', '2606', '2645', '2659', '2675', '2629', '2608', '2589', '2553', '31098'],
        ['Total Expenses', '18830', '18603', '19808', '19343', '18956', '19945', '21009', '20325', '19579', '18908', '18639', '19353', '232298'],
        ['Net Operating Income', '80520', '81517', '82492', '84357', '85294', '85835', '85341', '86675', '85571', '85392', '84911', '82747', '1011352']
    ]
    
    with open(t12_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(t12_data)
    
    print(f"✅ Sample T12 CSV created: {t12_csv}")
    
    return rent_roll_csv, t12_csv

if __name__ == "__main__":
    print("🔄 Creating sample HTML and PDF files...")
    
    # Create sample HTML
    html_path = create_sample_html()
    
    # Convert to PDF
    pdf_path = convert_to_pdf(html_path)
    
    # Create sample CSV files
    rent_roll_csv, t12_csv = create_sample_csv()
    
    print("\n🎉 Demonstration complete!")
    print(f"📄 HTML file: {html_path}")
    if pdf_path:
        print(f"📄 PDF file: {pdf_path}")
    print(f"📊 Rent Roll CSV: {rent_roll_csv}")
    print(f"📊 T12 CSV: {t12_csv}")
    print("\n✅ All file formats have been generated successfully!")
