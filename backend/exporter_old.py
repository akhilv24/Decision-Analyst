"""
Export Module
Handles data export to various formats including professional PDF reports.
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
    """Handles data export to various formats."""
    
    def __init__(self, df):
        """
        Initialize exporter with dataframe.
        
        Args:
            df (pd.DataFrame): Data to export
        """
        self.df = df.copy() if df is not None else None
    
    def export_to_csv(self, output_path):
        """
        Export data to CSV format.
        
        Args:
            output_path (str): Output file path
            
        Returns:
            bool: Success status
        """
        if self.df is None:
            logger.error("No data to export")
            return False
        
        try:
            self.df.to_csv(output_path, index=False)
            logger.info(f"Data exported to CSV: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error exporting to CSV: {str(e)}")
            return False
    
    def export_category_summary(self, output_path):
        """
        Export category-wise spending summary.
        
        Args:
            output_path (str): Output file path
            
        Returns:
            bool: Success status
        """
        if self.df is None or 'category' not in self.df.columns:
            return False
        
        try:
            category_summary = self.df.groupby('category')['amount'].agg([
                ('Total', 'sum'),
                ('Count', 'count'),
                ('Average', 'mean'),
                ('Min', 'min'),
                ('Max', 'max')
            ]).round(2).sort_values('Total', ascending=False)
            
            category_summary.to_csv(output_path)
            logger.info(f"Category summary exported to: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error exporting category summary: {str(e)}")
            return False
    
    def export_monthly_summary(self, output_path):
        """
        Export monthly spending summary.
        
        Args:
            output_path (str): Output file path
            
        Returns:
            bool: Success status
        """
        if self.df is None or 'date' not in self.df.columns:
            return False
        
        try:
            df_temp = self.df.copy()
            df_temp['date'] = pd.to_datetime(df_temp['date'])
            df_temp['month'] = df_temp['date'].dt.to_period('M')
            
            monthly_summary = df_temp.groupby('month')['amount'].agg([
                ('Total', 'sum'),
                ('Count', 'count'),
                ('Average', 'mean')
            ]).round(2)
            
            monthly_summary.to_csv(output_path)
            logger.info(f"Monthly summary exported to: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error exporting monthly summary: {str(e)}")
            return False
    
    def export_data_package(self, output_directory):
        """
        Export multiple files for data analysis.
        
        Args:
            output_directory (str): Directory to save exports
            
        Returns:
            dict: Export results with file paths
        """
        if self.df is None:
            logger.error("No data to export")
            return {}
        
        # Create output directory if it doesn't exist
        os.makedirs(output_directory, exist_ok=True)
        
        results = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Export main cleaned data
        main_file = os.path.join(output_directory, f"transactions_{timestamp}.csv")
        if self.export_to_csv(main_file):
            results['main_data'] = main_file
        
        # Export category summary
        if 'category' in self.df.columns:
            category_file = os.path.join(output_directory, f"category_summary_{timestamp}.csv")
            if self.export_category_summary(category_file):
                results['category_summary'] = category_file
        
        # Export monthly summary
        if 'date' in self.df.columns:
            monthly_file = os.path.join(output_directory, f"monthly_summary_{timestamp}.csv")
            if self.export_monthly_summary(monthly_file):
                results['monthly_summary'] = monthly_file
        
        logger.info(f"Data package exported to: {output_directory}")
        return results
    
    def get_export_metadata(self):
        """
        Get metadata about the exported data.
        
        Returns:
            dict: Export metadata
        """
        if self.df is None:
            return {}
        
        return {
            'total_records': len(self.df),
            'columns': list(self.df.columns),
            'date_range': f"{self.df['date'].min()} to {self.df['date'].max()}" if 'date' in self.df.columns else 'N/A',
            'file_size_kb': self.df.memory_usage(deep=True).sum() / 1024,
            'export_timestamp': datetime.now().isoformat()
        }

    def generate_professional_pdf(self, analysis_results, ai_insights=None):
        """
        Generate a professional PDF report with analysis data and AI insights.
        
        Args:
            analysis_results (dict): Analysis results from TransactionAnalyzer
            ai_insights (dict): AI insights from AIAnalyzer (optional)
            
        Returns:
            BytesIO: PDF document as byte stream, or None on error
        """
        try:
            from reportlab.lib.pagesizes import A4, letter
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.lib import colors
            from reportlab.platypus import Image
            
            # Create PDF buffer
            pdf_buffer = BytesIO()
            doc = SimpleDocTemplate(pdf_buffer, pagesize=A4, topMargin=0.4*inch, bottomMargin=0.4*inch, leftMargin=0.5*inch, rightMargin=0.5*inch)
            
            # Get styles and create custom ones
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=28,
                textColor=colors.HexColor('#0056b3'),
                spaceAfter=8,
                alignment=1,
                fontName='Helvetica-Bold'
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=13,
                textColor=colors.white,
                backColor=colors.HexColor('#0056b3'),
                spaceAfter=10,
                spaceBefore=12,
                leftIndent=8,
                fontName='Helvetica-Bold'
            )
            
            subheading_style = ParagraphStyle(
                'SubHeading',
                parent=styles['Heading3'],
                fontSize=11,
                textColor=colors.HexColor('#0056b3'),
                spaceAfter=8,
                fontName='Helvetica-Bold'
            )
            
            normal_style = ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=6,
                alignment=4  # Justify
            )
            
            # Build PDF content
            content = []
            
            # ===== HEADER SECTION =====
            content.append(Paragraph("DECISION ANALYST", title_style))
            content.append(Paragraph("Smart Finance Auditor - Professional Financial Analysis Report", styles['Normal']))
            content.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}", styles['Normal']))
            content.append(Spacer(1, 0.25*inch))
            
            # ===== FINANCIAL SUMMARY SECTION =====
            stats = analysis_results.get('summary_statistics', {})
            
            summary_data = [
                ['Financial Metric', 'Value'],
                ['Total Spending', f"Rs. {stats.get('total_spent', 0):,.2f}"],
                ['Total Transactions', f"{stats.get('total_transactions', 0):,}"],
                ['Average Transaction', f"Rs. {stats.get('average_transaction', 0):,.2f}"],
                ['Median Transaction', f"Rs. {stats.get('median_transaction', 0):,.2f}"],
                ['Highest Transaction', f"Rs. {stats.get('max_transaction', 0):,.2f}"],
                ['Lowest Transaction', f"Rs. {stats.get('min_transaction', 0):,.2f}"],
                ['Standard Deviation', f"Rs. {stats.get('std_deviation', 0):,.2f}"],
            ]
            
            summary_table = Table(summary_data, colWidths=[3.5*inch, 2.5*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0056b3')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f9fafb')),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#1f2937')),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f3f4f6')]),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
            ]))
            
            content.append(Paragraph("📊 Financial Summary", heading_style))
            content.append(summary_table)
            content.append(Spacer(1, 0.25*inch))
            
            # ===== SPENDING BY CATEGORY SECTION =====
            cat_analysis = analysis_results.get('category_analysis', {})
            if cat_analysis:
                cat_data = [['Category', 'Total Amount', 'Transactions', 'Average', 'Percentage']]
                total_amount = sum([v.get('total', 0) for v in cat_analysis.values()])
                
                sorted_categories = sorted(cat_analysis.items(), key=lambda x: x[1].get('total', 0), reverse=True)
                for cat, details in sorted_categories[:12]:  # Top 12 categories
                    total = details.get('total', 0)
                    count = details.get('count', 0)
                    average = details.get('average', 0)
                    percentage = (total / total_amount * 100) if total_amount > 0 else 0
                    
                    cat_data.append([
                        cat[:20],  # Truncate long category names
                        f"Rs. {total:,.2f}",
                        str(count),
                        f"Rs. {average:,.2f}",
                        f"{percentage:.1f}%"
                    ])
                
                cat_table = Table(cat_data, colWidths=[1.3*inch, 1.3*inch, 1*inch, 1.2*inch, 0.9*inch])
                cat_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0056b3')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f3f4f6')]),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
                ]))
                
                content.append(Paragraph("📈 Spending by Category", heading_style))
                content.append(cat_table)
                content.append(Spacer(1, 0.25*inch))
            
            # ===== AI INSIGHTS SECTION =====
            if ai_insights:
                content.append(Paragraph("🤖 AI-Powered Insights & Analysis", heading_style))
                
                # Executive Summary
                summary_text = ai_insights.get('summary', 'No summary available')
                if summary_text:
                    content.append(Paragraph(f"<b>Executive Summary:</b> {summary_text}", normal_style))
                    content.append(Spacer(1, 0.12*inch))
                
                # Smart Recommendations
                recommendations = ai_insights.get('recommendations', [])
                if recommendations:
                    content.append(Paragraph("💡 Smart Recommendations for Optimization:", subheading_style))
                    for i, rec in enumerate(recommendations[:8], 1):
                        # Safely handle string encoding
                        rec_text = str(rec) if rec else f"Recommendation {i}"
                        content.append(Paragraph(f"• {rec_text}", normal_style))
                    content.append(Spacer(1, 0.12*inch))
                
                # Anomalies & Risk Flags
                anomalies = ai_insights.get('anomalies', [])
                if anomalies:
                    content.append(Paragraph("⚠️ Detected Anomalies & Risk Flags:", subheading_style))
                    for i, anom in enumerate(anomalies[:8], 1):
                        # Safely handle string encoding
                        anom_text = str(anom) if anom else f"Anomaly {i}"
                        content.append(Paragraph(f"• {anom_text}", normal_style))
                    content.append(Spacer(1, 0.12*inch))
                
                # Spending Patterns
                patterns = ai_insights.get('patterns', [])
                if patterns:
                    content.append(Paragraph("📊 Identified Spending Patterns:", subheading_style))
                    for i, pattern in enumerate(patterns[:6], 1):
                        pattern_text = str(pattern) if pattern else f"Pattern {i}"
                        content.append(Paragraph(f"• {pattern_text}", normal_style))
                    content.append(Spacer(1, 0.12*inch))
                
                # Risk Level Summary if available
                risk_level = ai_insights.get('risk_level', None)
                if risk_level:
                    risk_color = colors.HexColor('#dc2626') if 'high' in str(risk_level).lower() else (colors.HexColor('#f59e0b') if 'medium' in str(risk_level).lower() else colors.HexColor('#10b981'))
                    content.append(Paragraph(f"<font color='#0056b3'><b>Overall Financial Health Risk Level:</b></font> <font color='{risk_color}'><b>{str(risk_level).upper()}</b></font>", normal_style))
                    content.append(Spacer(1, 0.12*inch))
            else:
                # If no AI insights available, add note
                content.append(Paragraph("🤖 AI-Powered Insights", heading_style))
                content.append(Paragraph("AI insights not available for this analysis.", normal_style))
                content.append(Spacer(1, 0.15*inch))
            
            # ===== AUDIT HIGHLIGHTS SECTION =====
            audit_metrics = analysis_results.get('audit_metrics', {})
            if audit_metrics:
                content.append(Paragraph("🔍 Audit Highlights", heading_style))
                
                audit_info = [
                    ['Metric', 'Value'],
                    ['Highest Spending Day', audit_metrics.get('highest_spending_date', 'N/A')],
                    ['Highest Transaction', f"Rs. {audit_metrics.get('highest_transaction_value', 0):,.2f}"],
                    ['Most Frequent Category', audit_metrics.get('most_frequent_category', 'N/A')],
                    ['Repeated Transactions', str(audit_metrics.get('repeated_transaction_count', 0))],
                ]
                
                audit_table = Table(audit_info, colWidths=[3.5*inch, 2.5*inch])
                audit_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0056b3')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f3f4f6')]),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ]))
                
                content.append(audit_table)
                content.append(Spacer(1, 0.25*inch))
            
            # ===== FOOTER SECTION =====
            content.append(Spacer(1, 0.2*inch))
            footer_text = "© 2025-2026 Decision Analyst. All rights reserved. | Powered by Advanced AI Analytics"
            content.append(Paragraph(footer_text, styles['Normal']))
            
            # Build PDF
            doc.build(content)
            pdf_buffer.seek(0)
            
            logger.info("Professional PDF generated successfully")
            return pdf_buffer
            
        except Exception as e:
            logger.error(f"Error generating professional PDF: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
