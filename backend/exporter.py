"""
Professional PDF Export Module
Generates structured financial dashboard PDFs matching professional reporting standards.
"""

import pandas as pd
import logging
import os
from datetime import datetime
from io import BytesIO
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataExporter:
    """Handles professional data export to PDF format."""
    
    def __init__(self, df):
        self.df = df.copy() if df is not None else None
    
    def export_to_csv(self, output_path):
        if self.df is None:
            return False
        try:
            self.df.to_csv(output_path, index=False)
            logger.info(f"Data exported to CSV: {output_path}")
            return True
        except Exception as e:
            logger.error(f"CSV export error: {str(e)}")
            return False
    
    def export_category_summary(self, output_path):
        if self.df is None:
            return False
        try:
            if 'category' in self.df.columns and 'amount' in self.df.columns:
                summary = self.df.groupby('category')['amount'].agg(['sum', 'count', 'mean']).reset_index()
                summary.to_csv(output_path, index=False)
                logger.info(f"Category summary exported: {output_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Category export error: {str(e)}")
            return False
    
    def _generate_bar_chart(self, cat_analysis):
        """Generate horizontal bar chart for top spending categories."""
        try:
            if not cat_analysis:
                return None
            
            categories = list(cat_analysis.keys())[:8]
            amounts = [cat_analysis[cat].get('total', 0) for cat in categories]
            
            fig, ax = plt.subplots(figsize=(10, 4))
            colors_list = ['#0056b3', '#0066cc', '#0077dd', '#0088ff', '#1199ff', '#22aaff', '#33bbff', '#44ccff']
            ax.barh(categories, amounts, color=colors_list[:len(categories)])
            ax.set_xlabel('Amount (Rs.)', fontsize=9, fontweight='bold')
            ax.set_title('Spend by Category', fontsize=11, fontweight='bold')
            ax.grid(axis='x', alpha=0.2)
            
            img_buffer = BytesIO()
            plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=100, facecolor='white')
            img_buffer.seek(0)
            plt.close(fig)
            return img_buffer
        except Exception as e:
            logger.warning(f"Bar chart failed: {str(e)}")
            return None
    
    def _generate_pie_chart(self, cat_analysis):
        """Generate pie chart for category distribution."""
        try:
            if not cat_analysis:
                return None
            
            categories = list(cat_analysis.keys())[:10]
            amounts = [cat_analysis[cat].get('total', 0) for cat in categories]
            
            fig, ax = plt.subplots(figsize=(7, 5))
            colors_list = ['#0056b3', '#0066cc', '#0077dd', '#0088ff', '#1199ff', '#22aaff', '#33bbff', '#44ccff', '#55ddff', '#66eeff']
            ax.pie(amounts, labels=categories, autopct='%1.1f%%', colors=colors_list[:len(categories)], startangle=90)
            ax.set_title('Category Distribution', fontsize=11, fontweight='bold')
            
            img_buffer = BytesIO()
            plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=100, facecolor='white')
            img_buffer.seek(0)
            plt.close(fig)
            return img_buffer
        except Exception as e:
            logger.warning(f"Pie chart failed: {str(e)}")
            return None
    
    def _generate_trend_chart(self, df):
        """Generate spending trend line chart."""
        try:
            if df is None or len(df) == 0:
                return None
            if 'date' not in df.columns or 'amount' not in df.columns:
                return None
            
            daily_spending = df.groupby(pd.to_datetime(df['date']).dt.date)['amount'].sum().sort_index()
            
            if len(daily_spending) == 0:
                return None
            
            fig, ax = plt.subplots(figsize=(11, 3))
            ax.plot(range(len(daily_spending)), daily_spending.values, marker='o', linewidth=2.5, 
                   color='#0056b3', markersize=5)
            ax.fill_between(range(len(daily_spending)), daily_spending.values, alpha=0.15, color='#0056b3')
            ax.set_ylabel('Amount (Rs.)', fontsize=9, fontweight='bold')
            ax.set_title('Spending Trend', fontsize=11, fontweight='bold')
            ax.grid(True, alpha=0.2)
            
            step = max(1, len(daily_spending) // 5)
            ax.set_xticks(range(0, len(daily_spending), step))
            ax.set_xticklabels([str(daily_spending.index[i]) for i in range(0, len(daily_spending), step)], 
                               rotation=45, fontsize=8)
            
            img_buffer = BytesIO()
            plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=100, facecolor='white')
            img_buffer.seek(0)
            plt.close(fig)
            return img_buffer
        except Exception as e:
            logger.warning(f"Trend chart failed: {str(e)}")
            return None
    
    def generate_professional_pdf(self, analysis_results, ai_insights=None, filename=None, file_size=None):
        """Generate classic financial report PDF - simple and clean CFO style."""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.lib import colors
            
            pdf_buffer = BytesIO()
            doc = SimpleDocTemplate(pdf_buffer, pagesize=A4, topMargin=0.75*inch, 
                                   bottomMargin=0.75*inch, leftMargin=0.75*inch, rightMargin=0.75*inch)
            
            styles = getSampleStyleSheet()
            content = []
            
            # Title and Header
            title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=16, 
                                        textColor=colors.HexColor('#0056b3'), spaceAfter=4, 
                                        alignment=1, fontName='Helvetica-Bold')
            subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'], fontSize=10, 
                                           textColor=colors.HexColor('#666'), spaceAfter=12, alignment=1)
            file_info_style = ParagraphStyle('FileInfo', parent=styles['Normal'], fontSize=8, 
                                            textColor=colors.HexColor('#999'), spaceAfter=8, alignment=1)
            heading_style = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=12, 
                                          textColor=colors.HexColor('#0056b3'), spaceAfter=8, 
                                          spaceBefore=12, fontName='Helvetica-Bold')
            normal_style = ParagraphStyle('Normal', parent=styles['Normal'], fontSize=9, spaceAfter=4)
            
            # Header
            content.append(Paragraph("FINANCIAL ANALYSIS REPORT", title_style))
            content.append(Paragraph(f"Decision Analyst - {datetime.now().strftime('%B %d, %Y')}", subtitle_style))
            
            # File Info
            if filename and file_size:
                file_size_kb = file_size / 1024 if file_size > 0 else 0
                file_info = f"Source File: {filename} | File Size: {file_size_kb:.1f} KB"
                content.append(Paragraph(file_info, file_info_style))
            
            content.append(Spacer(1, 0.2*inch))
            
            # Overall Summary
            stats = analysis_results.get('summary_statistics', {})
            content.append(Paragraph("OVERALL EXPENSE SUMMARY", heading_style))
            
            summary_data = [
                ['Metric', 'Value'],
                ['Total Spending', f"Rs. {stats.get('total_spent', 0):,.0f}"],
                ['Total Transactions', f"{stats.get('total_transactions', 0):,}"],
                ['Average Transaction', f"Rs. {stats.get('average_transaction', 0):,.0f}"],
                ['Highest Transaction', f"Rs. {stats.get('max_transaction', 0):,.0f}"],
                ['Lowest Transaction', f"Rs. {stats.get('min_transaction', 0):,.0f}"],
            ]
            
            summary_table = Table(summary_data, colWidths=[3.5*inch, 2*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0056b3')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#ccc')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            
            content.append(summary_table)
            content.append(Spacer(1, 0.2*inch))
            
            # Category Breakdown
            content.append(Paragraph("EXPENSE BY CATEGORY", heading_style))
            
            cat_analysis = analysis_results.get('category_analysis', {})
            cat_data = [['Category', 'Amount', 'Count', 'Percentage']]
            total_amount = stats.get('total_spent', 1)
            
            for cat, info in sorted(cat_analysis.items(), key=lambda x: x[1].get('total', 0), reverse=True)[:10]:
                amount = info.get('total', 0)
                count = info.get('count', 0)
                pct = (amount / total_amount * 100) if total_amount > 0 else 0
                cat_data.append([
                    cat,
                    f"Rs. {amount:,.0f}",
                    str(count),
                    f"{pct:.1f}%"
                ])
            
            cat_table = Table(cat_data, colWidths=[2*inch, 1.5*inch, 1*inch, 1*inch])
            cat_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0056b3')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#ccc')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            
            content.append(cat_table)
            content.append(Spacer(1, 0.2*inch))
            
            # CFO Report Section
            content.append(PageBreak())
            content.append(Paragraph("CFO EXECUTIVE REPORT", heading_style))
            content.append(Spacer(1, 0.1*inch))
            
            if ai_insights:
                # Risk Level
                risk_level = ai_insights.get('risk_level', 'MEDIUM').upper()
                content.append(Paragraph(f"<b>Financial Health Risk Level: {risk_level}</b>", normal_style))
                content.append(Spacer(1, 0.08*inch))
                
                # Summary
                summary = ai_insights.get('summary', '')
                if summary:
                    content.append(Paragraph(f"<b>Executive Summary</b>", normal_style))
                    content.append(Paragraph(summary, normal_style))
                    content.append(Spacer(1, 0.1*inch))
                
                # Spending Patterns
                patterns = ai_insights.get('patterns', [])
                if patterns:
                    content.append(Paragraph("<b>Spending Patterns</b>", normal_style))
                    for p in patterns[:5]:
                        content.append(Paragraph(f"• {str(p)}", normal_style))
                    content.append(Spacer(1, 0.1*inch))
                
                # Recommendations
                recs = ai_insights.get('recommendations', [])
                if recs:
                    content.append(Paragraph("<b>CFO Recommendations</b>", normal_style))
                    for i, r in enumerate(recs[:8], 1):
                        content.append(Paragraph(f"{i}. {str(r)}", normal_style))
                    content.append(Spacer(1, 0.1*inch))
                
                # Anomalies/Risk Flags
                anom = ai_insights.get('anomalies', [])
                if anom:
                    content.append(Paragraph("<b>Risk Flags & Anomalies</b>", normal_style))
                    for a in anom[:5]:
                        content.append(Paragraph(f"⚠️  {str(a)}", normal_style))
            
            content.append(Spacer(1, 0.2*inch))
            content.append(Paragraph(
                f"Generated: {datetime.now().strftime('%B %d, %Y at %H:%M')} | Decision Analyst Financial Analysis System",
                ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, 
                             textColor=colors.HexColor('#999'), alignment=0)
            ))
            
            doc.build(content)
            pdf_buffer.seek(0)
            logger.info("Classic financial report PDF generated successfully")
            return pdf_buffer
            
        except Exception as e:
            logger.error(f"PDF generation error: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
