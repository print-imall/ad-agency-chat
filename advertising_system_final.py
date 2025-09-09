import streamlit as st
import pandas as pd
import os
from PIL import Image
from pathlib import Path
import re
from io import BytesIO
import requests
from urllib.parse import urlparse
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def apply_custom_css():
    st.markdown("""
    <style>
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 0rem 1rem;
    }
    
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    h1 {
        background: linear-gradient(90deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        text-align: center;
        margin-bottom: 2rem;
        font-size: 3rem !important;
    }
    
    .stButton > button {
        background: linear-gradient(45deg, #667eea, #764ba2);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 16px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px 0 rgba(102, 126, 234, 0.4);
        width: 100%;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px 0 rgba(102, 126, 234, 0.6);
        background: linear-gradient(45deg, #764ba2, #667eea);
    }
    
    .metric-container {
        background: rgba(255, 255, 255, 0.9);
        padding: 1rem;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 4px 15px 0 rgba(31, 38, 135, 0.2);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        transition: all 0.3s ease;
    }
    
    @keyframes float {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
        100% { transform: translateY(0px); }
    }
    
    .floating {
        animation: float 3s ease-in-out infinite;
    }
    
    .github-info {
        background: rgba(40, 167, 69, 0.1);
        border: 1px solid rgba(40, 167, 69, 0.3);
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

class FixedEnhancedSystem:
    def __init__(self):
        self.df = None
        self.image_index = {}
        self.columns_map = {}
        # קובץ ברירת המחדל מ-GitHub
        self.default_github_url = "https://raw.githubusercontent.com/print-imall/ad-agency-chat/main/campaigns_data.xlsx"
    
    def clear_cache(self):
        try:
            keys_to_remove = []
            for key in st.session_state.keys():
                if key.startswith(('last_gantt', 'history', 'search_results')):
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del st.session_state[key]
            
            st.cache_data.clear()
            st.cache_resource.clear()
            
            self.df = None
            self.image_index = {}
            self.columns_map = {}
            
            return "✅ Cache נוקה בהצלחה!"
        except Exception as e:
            return f"❌ שגיאה בניקוי Cache: {e}"

    def convert_github_url_to_raw(self, github_url):
        """המרת URL של GitHub לכתובת הקובץ הגולמי"""
        if "raw.githubusercontent.com" in github_url:
            return github_url
        
        if "github.com" in github_url and "/blob/" in github_url:
            return github_url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
        
        return github_url

    def load_data_from_github(self, github_url=None):
        """טעינת קובץ Excel מ-GitHub"""
        if github_url is None:
            github_url = self.default_github_url
        
        try:
            # המרת ה-URL לפורמט הגולמי
            raw_url = self.convert_github_url_to_raw(github_url)
            
            # הורדת הקובץ
            response = requests.get(raw_url, timeout=30)
            response.raise_for_status()
            
            # יצירת BytesIO object מהתוכן
            excel_buffer = BytesIO(response.content)
            
            # טעינת הקובץ
            self.df = pd.read_excel(excel_buffer, engine='openpyxl')
            self.df = self.clean_data()
            
            # הדפסת דיבוג לבדיקת מבנה הקובץ
            st.write("📋 **מבנה הקובץ שנטען מ-GitHub:**")
            st.write(f"📊 מספר שורות: {len(self.df)}")
            st.write(f"📋 מספר עמודות: {len(self.df.columns)}")
            
            st.write("📝 **רשימת כל העמודות:**")
            for i, col in enumerate(self.df.columns):
                st.write(f"  {i+1}. '{col}' (סוג: {self.df[col].dtype})")
            
            # יצירת המיפוי אחרי הדיבוג
            self.create_column_mapping()
            
            # הצגת דוגמה מהנתונים - רק עמודות חשובות
            st.write("👀 **דוגמה מהנתונים:**")
            if len(self.df.columns) >= 10:
                # הצגת עמודות ספציפיות שחשובות לנו
                display_cols = [self.df.columns[0], self.df.columns[2], self.df.columns[9]]  # מתחם, פלטפורמה, קמפיין
                sample_df = self.df[display_cols].head(5)
                st.dataframe(sample_df)
                
                # בדיקה ספציפית של עמודת הקמפיין
                campaign_col = self.df.columns[9]  # עמודה 10 = אינדקס 9
                st.write(f"🎯 **בדיקת עמודת הקמפיין '{campaign_col}':**")
                unique_campaigns = self.df[campaign_col].dropna().unique()
                st.write(f"ערכים ייחודיים: {list(unique_campaigns)}")
                
                # ספירה של כל ערך
                campaign_counts = self.df[campaign_col].value_counts()
                st.write("📊 **ספירת ערכים בעמודת קמפיין:**")
                for value, count in campaign_counts.items():
                    st.write(f"  - '{value}': {count} פריטים")
            else:
                st.dataframe(self.df.head(3))
            
            st.success(f"✅ נטען קובץ מ-GitHub עם {len(self.df)} פריטים")
            return True
            
        except requests.RequestException as e:
            st.error(f"❌ שגיאה בהורדת הקובץ מ-GitHub: {e}")
            return False
        except Exception as e:
            st.error(f"❌ שגיאה בטעינת הקובץ: {e}")
            return False

    def load_excel_data(self, uploaded_file):
        """טעינת קובץ Excel מהעלאה מקומית"""
        try:
            self.df = pd.read_excel(uploaded_file, engine='openpyxl')
            self.df = self.clean_data()
            
            # הדפסת דיבוג לבדיקת מבנה הקובץ
            st.write("📋 **מבנה הקובץ שנטען:**")
            st.write(f"📊 מספר שורות: {len(self.df)}")
            st.write(f"📋 מספר עמודות: {len(self.df.columns)}")
            
            st.write("📝 **רשימת כל העמודות:**")
            for i, col in enumerate(self.df.columns):
                st.write(f"  {i+1}. '{col}' (סוג: {self.df[col].dtype})")
            
            # יצירת המיפוי אחרי הדיבוג
            self.create_column_mapping()
            
            # הצגת דוגמה מהנתונים - רק עמודות חשובות
            st.write("👀 **דוגמה מהנתונים:**")
            if len(self.df.columns) >= 10:
                # הצגת עמודות ספציפיות שחשובות לנו
                display_cols = [self.df.columns[0], self.df.columns[2], self.df.columns[9]]  # מתחם, פלטפורמה, קמפיין
                sample_df = self.df[display_cols].head(5)
                st.dataframe(sample_df)
                
                # בדיקה ספציפית של עמודת הקמפיין
                campaign_col = self.df.columns[9]  # עמודה 10 = אינדקס 9
                st.write(f"🎯 **בדיקת עמודת הקמפיין '{campaign_col}':**")
                unique_campaigns = self.df[campaign_col].dropna().unique()
                st.write(f"ערכים ייחודיים: {list(unique_campaigns)}")
                
                # ספירה של כל ערך
                campaign_counts = self.df[campaign_col].value_counts()
                st.write("📊 **ספירת ערכים בעמודת קמפיין:**")
                for value, count in campaign_counts.items():
                    st.write(f"  - '{value}': {count} פריטים")
            else:
                st.dataframe(self.df.head(3))
            
            st.success(f"✅ נטען קובץ עם {len(self.df)} פריטים")
            return True
        except Exception as e:
            st.error(f"❌ שגיאה בטעינת הקובץ: {e}")
            return False

    def clean_data(self):
        df = self.df.copy()
        for col in df.columns:
            df[col] = df[col].astype(str).str.strip()
        df = df.dropna(how='all')
        df.columns = [str(col).strip() for col in df.columns]
        return df

    def create_column_mapping(self):
        columns = list(self.df.columns)
        self.columns_map = {}
        
        if len(columns) >= 9:
            self.columns_map = {
                'location': columns[0],
                'item_code': columns[1],
                'platform': columns[2],
                'price': columns[3],
                'visitors': columns[4],
                'height': columns[5],
                'width': columns[6],
                'height2': columns[7],
                'width2': columns[8]
            }

    def index_images(self, image_folder):
        if not os.path.exists(image_folder):
            st.warning(f"תיקיית התמונות לא נמצאה: {image_folder}")
            return
        
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        self.image_index = {}
        
        for file_path in Path(image_folder).glob('*'):
            if file_path.suffix.lower() in image_extensions:
                item_code = file_path.stem
                self.image_index[item_code] = str(file_path)
        
        st.success(f"נמצאו {len(self.image_index)} תמונות")

    def smart_search(self, query):
        if self.df is None:
            return "❌ לא נטענו נתונים עדיין"
        
        query_clean = query.strip()
        query_parts = self.split_query(query_clean)
        
        best_match = None
        best_score = 0
        
        for idx, row in self.df.iterrows():
            score = 0
            matching_details = []
            matched_parts = 0
            
            for part in query_parts:
                part_lower = part.lower()
                found = False
                
                for field_name, col_name in self.columns_map.items():
                    field_value = str(row[col_name]).lower()
                    
                    if part_lower in field_value:
                        hebrew_name = self.get_hebrew_name(field_name)
                        matching_details.append(f"'{part}' נמצא ב'{hebrew_name}")
                        found = True
                        score += 50
                        break
                
                if found:
                    matched_parts += 1
            
            if matched_parts == len(query_parts) and score > best_score:
                best_score = score
                best_match = {
                    'row': row,
                    'score': score,
                    'matching_details': matching_details
                }
        
        if not best_match:
            return f"❌ לא נמצאה שורה שמכילה את כל החלקים: {', '.join(query_parts)}"
        
        return self.format_result(best_match, query_clean)

    def build_gantt_by_budget(self, budget, target_locations=None):
        if self.df is None:
            return "❌ לא נטענו נתונים עדיין"
        
        try:
            budget = float(budget)
        except:
            return "❌ תקציב חייב להיות מספר"
        
        df_filtered = self.df.copy()
        if target_locations:
            location_col = self.columns_map['location']
            df_filtered = df_filtered[df_filtered[location_col].str.contains('|'.join(target_locations), case=False, na=False)]
        
        price_col = self.columns_map['price']
        df_filtered['price_numeric'] = pd.to_numeric(
            df_filtered[price_col].astype(str).str.replace(r'[^\d.]', '', regex=True),
            errors='coerce'
        ).fillna(0)
        
        df_sorted = df_filtered.sort_values('price_numeric')
        
        selected_items = []
        current_total = 0
        
        for idx, row in df_sorted.iterrows():
            item_price = row['price_numeric']
            if current_total + item_price <= budget:
                selected_items.append(row)
                current_total += item_price
                
                if current_total >= budget * 0.95:
                    break
        
        if not selected_items:
            return f"❌ לא נמצאו אלמנטים שמתאימים לתקציב {budget:,.0f} ש״ח"
        
        return self.format_gantt_result(selected_items, current_total, budget, "תקציב")

    def build_gantt_by_campaign_type(self, campaign_type, budget=None, target_locations=None):
        if self.df is None:
            return "❌ לא נטענו נתונים עדיין"
        
        if campaign_type.lower() == "דיגיטלי":
            keywords = ['פייסבוק', 'אינסטגרם', 'גוגל', 'דיגיטל', 'פריימלס', 'וויז']
        elif campaign_type.lower() == "פרינט":
            keywords = ['בילבורד', 'חוצות', 'עיתון', 'מודעה', 'פוסטר', 'שלט']
        elif campaign_type.lower() == "משולב":
            digital_keywords = ['פייסבוק', 'אינסטגרם', 'גוגל', 'דיגיטל', 'פריימלס', 'וויז']
            print_keywords = ['בילבורד', 'חוצות', 'עיתון', 'מודעה', 'פוסטר', 'שלט']
            keywords = digital_keywords + print_keywords
        else:
            return f"❌ סוג קמפיין לא מוכר: {campaign_type}"
        
        platform_col = self.columns_map['platform']
        df_filtered = self.df[
            self.df[platform_col].str.contains('|'.join(keywords), case=False, na=False)
        ]
        
        if target_locations and len(target_locations) > 0:
            location_col = self.columns_map['location']
            df_filtered = df_filtered[df_filtered[location_col].str.contains('|'.join(target_locations), case=False, na=False)]
        
        if df_filtered.empty:
            location_text = f" במתחמים שנבחרו" if target_locations and len(target_locations) > 0 else ""
            return f"❌ לא נמצאו אלמנטים מסוג {campaign_type}{location_text}"
        
        price_col = self.columns_map['price']
        df_filtered['price_numeric'] = pd.to_numeric(
            df_filtered[price_col].astype(str).str.replace(r'[^\d.]', '', regex=True),
            errors='coerce'
        ).fillna(0)
        
        if budget:
            try:
                budget = float(budget)
                df_sorted = df_filtered.sort_values('price_numeric')
                
                selected_items = []
                current_total = 0
                
                for idx, row in df_sorted.iterrows():
                    item_price = row['price_numeric']
                    if current_total + item_price <= budget:
                        selected_items.append(row)
                        current_total += item_price
                        
                        if current_total >= budget * 0.95:
                            break
                
                if not selected_items:
                    location_text = f" במתחמים שנבחרו" if target_locations and len(target_locations) > 0 else ""
                    return f"❌ לא נמצאו אלמנטים מסוג {campaign_type} שמתאימים לתקציב {budget:,.0f} ש״ח{location_text}"
                
                return self.format_gantt_result(selected_items, current_total, budget, f"{campaign_type} עם תקציב")
            except:
                pass
        
        selected_items = df_filtered.to_dict('records')
        total_cost = df_filtered['price_numeric'].sum()
        
        location_text = f" במתחמים שנבחרו" if target_locations and len(target_locations) > 0 else ""
        return self.format_gantt_result(selected_items, total_cost, None, f"{campaign_type}{location_text}")

    def format_gantt_result(self, items, total_cost, budget, gantt_type):
        num_items = len(items)
        
        result_text = f"📊 **גנט פרסום - {gantt_type}**\n\n"
        
        if budget:
            result_text += f"💰 **תקציב:** {budget:,.0f} ש״ח\n"
            result_text += f"💵 **עלות כוללת:** {total_cost:,.0f} ש״ח\n"
            result_text += f"📈 **ניצול תקציב:** {(total_cost/budget)*100:.1f}%\n"
        else:
            result_text += f"💵 **עלות כוללת:** {total_cost:,.0f} ש״ח\n"
        
        result_text += f"📋 **מספר אלמנטים:** {num_items}\n\n"
        
        table_data = []
        images_to_show = []
        
        for i, item in enumerate(items, 1):
            table_row = {
                'מס\'': i,
                'מק"ט': item[self.columns_map['item_code']],
                'מתחם': item[self.columns_map['location']],
                'פלטפורמה': item[self.columns_map['platform']],
                'מחיר מכירה': self.format_price(item[self.columns_map['price']]),
                'מבקרים': self.format_number(item[self.columns_map['visitors']]),
                'גובה': self.format_dimension(item[self.columns_map['height']]),
                'רוחב': self.format_dimension(item[self.columns_map['width']])
            }
            
            height2 = self.format_dimension(item[self.columns_map['height2']])
            width2 = self.format_dimension(item[self.columns_map['width2']])
            
            if height2 not in ["0", "0.0"]:
                table_row['גובה2'] = height2
            if width2 not in ["0", "0.0"]:
                table_row['רוחב2'] = width2
            
            table_data.append(table_row)
            
            if i <= 10:
                item_code = str(item[self.columns_map['item_code']])
                if item_code in self.image_index:
                    images_to_show.append((item_code, self.image_index[item_code]))
        
        return result_text, table_data, images_to_show

    def create_excel_export(self, table_data, title, include_price=True):
        buffer = BytesIO()
        
        if not table_data:
            df_empty = pd.DataFrame({"הודעה": ["אין נתונים להצגה"]})
            df_empty.to_excel(buffer, index=False, engine='openpyxl')
        else:
            df = pd.DataFrame(table_data)
            
            if not include_price:
                columns_to_remove = ['מק"ט', 'מחיר מכירה']
                for col in columns_to_remove:
                    if col in df.columns:
                        df = df.drop(columns=[col])
            
            df.to_excel(buffer, index=False, engine='openpyxl', sheet_name=title[:30])
        
        buffer.seek(0)
        return buffer

    def create_pdf_export(self, table_data, title, include_price=True):
        buffer = BytesIO()
        
        try:
            # ניסיון ליבא ספריות לעברית
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            
            # ניסיון לטעון פונט עברי מהמערכת
            hebrew_font_loaded = False
            
            # רשימת פונטים עבריים אפשריים במערכת
            hebrew_fonts = [
                'C:/Windows/Fonts/arial.ttf',
                'C:/Windows/Fonts/calibri.ttf', 
                'C:/Windows/Fonts/tahoma.ttf',
                '/System/Library/Fonts/Arial.ttf',  # Mac
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'  # Linux
            ]
            
            for font_path in hebrew_fonts:
                try:
                    if os.path.exists(font_path):
                        pdfmetrics.registerFont(TTFont('HebrewFont', font_path))
                        hebrew_font_loaded = True
                        break
                except:
                    continue
            
            if not hebrew_font_loaded:
                st.warning("⚠️ לא נמצא פונט עברי במערכת. ה-PDF יוצג באנגלית.")
                return self.create_simple_pdf_export(table_data, title, include_price)
            
        except ImportError:
            st.warning("⚠️ חסרות ספריות לפונט עברי. ה-PDF יוצג באנגלית.")
            return self.create_simple_pdf_export(table_data, title, include_price)
        
        # יצירת PDF עם פונט עברי
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        
        styles = getSampleStyleSheet()
        
        # סגנון עברי מותאם
        hebrew_style = ParagraphStyle(
            'Hebrew',
            parent=styles['Normal'],
            fontName='HebrewFont',
            fontSize=12,
            alignment=2,  # יישור לימין
            wordWrap='RTL'
        )
        
        title_style = ParagraphStyle(
            'HebrewTitle',
            parent=styles['Heading1'],
            fontName='HebrewFont',
            fontSize=16,
            spaceAfter=30,
            alignment=1  # מרכז
        )
        
        # כותרת בעברית
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 20))
        
        if not table_data:
            story.append(Paragraph("אין נתונים להצגה", hebrew_style))
        else:
            df = pd.DataFrame(table_data)
            
            if not include_price:
                columns_to_remove = ['מק"ט', 'מחיר מכירה']
                for col in columns_to_remove:
                    if col in df.columns:
                        df = df.drop(columns=[col])
            
            # יצירת טבלה עם נתונים עבריים
            table_values = []
            
            # כותרות
            headers = list(df.columns)
            table_values.append(headers)
            
            # תוכן
            for _, row in df.iterrows():
                row_data = [str(cell) for cell in row]
                table_values.append(row_data)
            
            table = Table(table_values, repeatRows=1)
            
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'HebrewFont'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('TOPPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                ('FONTNAME', (0, 1), (-1, -1), 'HebrewFont'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.lightgrey, colors.white])
            ]))
            
            story.append(table)
        
        # תאריך בעברית
        from datetime import datetime
        story.append(Spacer(1, 30))
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")
        story.append(Paragraph(f"נוצר בתאריך: {timestamp}", hebrew_style))
        
        try:
            doc.build(story)
            buffer.seek(0)
            return buffer
        except Exception as e:
            st.error(f"שגיאה ביצירת PDF עברי: {e}")
            return self.create_simple_pdf_export(table_data, title, include_price)

    def create_simple_pdf_export(self, table_data, title, include_price=True):
        """גיבוי - PDF פשוט באנגלית"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1,
            fontName='Helvetica-Bold'
        )
        
        # כותרת באנגלית
        english_title = f"Advertising Campaign Report - {len(table_data) if table_data else 0} Items"
        story.append(Paragraph(english_title, title_style))
        story.append(Spacer(1, 20))
        
        if not table_data:
            story.append(Paragraph("No data available", styles['Normal']))
        else:
            df = pd.DataFrame(table_data)
            
            if not include_price:
                columns_to_remove = ['מק"ט', 'מחיר מכירה']
                for col in columns_to_remove:
                    if col in df.columns:
                        df = df.drop(columns=[col])
            
            # המרת כותרות לאנגלית
            column_translation = {
                'מס\'': 'No.',
                'מק"ט': 'Item Code',
                'מתחם': 'Location',
                'פלטפורמה': 'Platform', 
                'מחיר מכירה': 'Price',
                'מבקרים': 'Visitors',
                'גובה': 'Height',
                'רוחב': 'Width',
                'גובה2': 'Height2',
                'רוחב2': 'Width2'
            }
            
            df_english = df.copy()
            for hebrew_col, english_col in column_translation.items():
                if hebrew_col in df_english.columns:
                    df_english = df_english.rename(columns={hebrew_col: english_col})
            
            table_values = [list(df_english.columns)]
            for _, row in df_english.iterrows():
                table_values.append([str(cell) for cell in row])
            
            table = Table(table_values, repeatRows=1)
            
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('TOPPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.lightgrey, colors.white])
            ]))
            
            story.append(table)
        
        from datetime import datetime
        story.append(Spacer(1, 30))
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")
        story.append(Paragraph(f"Generated on: {timestamp}", styles['Normal']))
        
        doc.build(story)
        buffer.seek(0)
        return buffer

    def split_query(self, query):
        item_codes = re.findall(r'\b\d{6,}\b', query)
        for code in item_codes:
            query = query.replace(code, '').strip()
        
        platform_patterns = ['פריימלס', 'פייסבוק', 'אינסטגרם', 'גוגל']
        platforms_found = []
        
        for platform in platform_patterns:
            pattern = rf'\b{platform}\s*\d*\b'
            matches = re.findall(pattern, query, re.IGNORECASE)
            for match in matches:
                platforms_found.append(match.strip())
                query = query.replace(match, '').strip()
        
        remaining = [word.strip() for word in query.split() if word.strip()]
        all_parts = item_codes + platforms_found + remaining
        return [part for part in all_parts if len(part) > 1]

    def get_hebrew_name(self, field_name):
        names = {
            'location': 'מתחם',
            'item_code': 'מק"ט',
            'platform': 'פלטפורמה',
            'price': 'מחיר',
            'visitors': 'מבקרים',
            'height': 'גובה',
            'width': 'רוחב'
        }
        return names.get(field_name, field_name)

    def format_result(self, match, query):
        row = match['row']
        
        result_text = f"🔍 **תוצאה עבור '{query}':**\n\n"
        result_text += "✅ **איך נמצאה ההתאמה:**\n"
        for detail in match['matching_details']:
            result_text += f"• {detail}\n"
        result_text += "\n"
        
        table_data = {
            'מק"ט': row[self.columns_map['item_code']],
            'מתחם': row[self.columns_map['location']],
            'פלטפורמה': row[self.columns_map['platform']],
            'מחיר מכירה': self.format_price(row[self.columns_map['price']]),
            'מבקרים': self.format_number(row[self.columns_map['visitors']]),
            'גובה': self.format_dimension(row[self.columns_map['height']]),
            'רוחב': self.format_dimension(row[self.columns_map['width']])
        }
        
        height2 = self.format_dimension(row[self.columns_map['height2']])
        width2 = self.format_dimension(row[self.columns_map['width2']])
        
        if height2 not in ["0", "0.0"]:
            table_data['גובה2'] = height2
        if width2 not in ["0", "0.0"]:
            table_data['רוחב2'] = width2
        
        item_code = str(row[self.columns_map['item_code']])
        image_path = None
        if item_code in self.image_index:
            image_path = self.image_index[item_code]
        
        return result_text, [table_data], image_path

    def format_price(self, price_str):
        try:
            clean_price = re.sub(r'[^\d.]', '', str(price_str))
            if clean_price:
                price_num = float(clean_price)
                return f"{price_num:,.0f} ש\"ח"
            return str(price_str)
        except:
            return str(price_str)

    def format_number(self, num_str):
        try:
            clean_num = re.sub(r'[^\d.]', '', str(num_str))
            if clean_num:
                num = float(clean_num)
                return f"{num:,.0f}"
            return str(num_str)
        except:
            return str(num_str)

    def format_dimension(self, dim_str):
        try:
            clean_dim = re.sub(r'[^\d.]', '', str(dim_str))
            if clean_dim:
                dim = float(clean_dim)
                return str(int(dim)) if dim == int(dim) else str(dim)
            return str(dim_str)
        except:
            return str(dim_str)

    def display_image(self, image_path):
        try:
            image = Image.open(image_path)
            st.image(image, use_container_width=True)
            return True
        except Exception as e:
            st.warning(f"לא ניתן להציג תמונה: {e}")
            return False

def main():
    st.set_page_config(
        page_title="מערכת פרסום מתקדמת", 
        page_icon="🚀", 
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    apply_custom_css()
    
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1 class="floating">🚀 מערכת פרסום מתקדמת</h1>
        <p style="font-size: 1.2rem; color: #667eea; font-weight: 500;">
            מערכת חכמה לחיפוש, בניית גנט ונידול קמפיינים פרסומיים
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    if 'enhanced_search' not in st.session_state:
        st.session_state.enhanced_search = FixedEnhancedSystem()
    
    search_system = st.session_state.enhanced_search
    
    with st.sidebar:
        st.markdown("### 📂 טעינת נתונים")
        
        # אפשרות לטעינת קובץ מ-GitHub
        st.markdown('<div class="github-info">', unsafe_allow_html=True)
        st.markdown("**🌐 טעינה מ-GitHub (מומלץ)**")
        st.markdown("הקובץ יטען אוטומטיש מהמאגר")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🚀 טען נתונים מ-GitHub", use_container_width=True):
                with st.spinner("מוריד קובץ מ-GitHub..."):
                    if search_system.load_data_from_github():
                        st.balloons()
        
        with col2:
            # אפשרות לטעינת URL מותאם אישית
            custom_url = st.text_input("🔗 או הכנס URL מותאם", 
                                     placeholder="https://raw.githubusercontent.com/...")
            if custom_url and st.button("🔗 טען מ-URL", use_container_width=True):
                with st.spinner("מוריד קובץ..."):
                    if search_system.load_data_from_github(custom_url):
                        st.balloons()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # אפשרות טעינה מקומית
        st.markdown("**📁 טעינה מקומית**")
        uploaded_file = st.file_uploader("בחר קובץ Excel", type=['xlsx', 'xls'])
        
        if uploaded_file:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📊 טען נתונים", use_container_width=True):
                    with st.spinner("טוען נתונים..."):
                        if search_system.load_excel_data(uploaded_file):
                            st.balloons()
            with col2:
                if st.button("🗑️ נקה Cache", use_container_width=True):
                    result = search_system.clear_cache()
                    st.success(result)
                    st.rerun()
        
        st.markdown("---")
        
        st.markdown("### 🖼️ תמונות")
        image_folder = st.text_input("נתיב לתיקיית התמונות")
        
        if image_folder and st.button("🔍 טען תמונות", use_container_width=True):
            search_system.index_images(image_folder)
        
        if search_system.df is not None:
            st.markdown("---")
            st.markdown("### 📊 סטטיסטיקות")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"""
                <div class="metric-container">
                    <h3 style="color: #667eea; margin: 0;">📋</h3>
                    <h2 style="margin: 0.5rem 0;">{len(search_system.df):,}</h2>
                    <p style="margin: 0; color: #666;">פריטים</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="metric-container">
                    <h3 style="color: #764ba2; margin: 0;">🖼️</h3>
                    <h2 style="margin: 0.5rem 0;">{len(search_system.image_index):,}</h2>
                    <p style="margin: 0; color: #666;">תמונות</p>
                </div>
                """, unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["🔍 חיפוש חכם", "📊 בניית גנט", "📄 ייצוא מתקדם"])
    
    with tab1:
        if search_system.df is None:
            st.info("טען נתונים מ-GitHub או העלה קובץ Excel כדי להתחיל")
        else:
            if 'history' not in st.session_state:
                st.session_state.history = []
            
            for message in st.session_state.history:
                if message['role'] == 'user':
                    with st.chat_message("user"):
                        st.write(message['content'])
                else:
                    with st.chat_message("assistant"):
                        st.markdown(message['content'])
                        
                        if 'table' in message:
                            st.dataframe(pd.DataFrame(message['table']), use_container_width=True)
                        
                        if 'image' in message:
                            search_system.display_image(message['image'])
            
            user_input = st.chat_input("🔍 שאל שאלה או חפש משהו...")
            
            if user_input:
                st.session_state.history.append({'role': 'user', 'content': user_input})
                
                if search_system.df is not None:
                    with st.spinner("🔍 מחפש..."):
                        result = search_system.smart_search(user_input)
                        
                        if isinstance(result, tuple):
                            text, table, image = result
                            msg = {'role': 'assistant', 'content': text, 'table': table}
                            if image:
                                msg['image'] = image
                            st.session_state.history.append(msg)
                        else:
                            st.session_state.history.append({'role': 'assistant', 'content': result})
                    
                    st.rerun()
                else:
                    st.error("❌ אנא טען קובץ נתונים תחילה")
                    st.session_state.history.pop()
    
    with tab2:
        if search_system.df is None:
            st.warning("טען נתונים כדי לבנות גנט")
        else:
            gantt_type = st.selectbox("בחר סוג גנט:", ["גנט לפי תקציב", "גנט לפי סוג קמפיין"])
            
            if gantt_type == "גנט לפי תקציב":
                col1, col2 = st.columns([2, 3])
                
                with col1:
                    budget = st.number_input("💰 תקציב (ש״ח)", min_value=0, value=50000, step=1000)
                
                with col2:
                    if 'location' in search_system.columns_map:
                        location_col = search_system.columns_map['location']
                        all_locations = search_system.df[location_col].unique()
                        selected_locations = st.multiselect("🗺️ בחר מתחמים (אופציונלי)", all_locations)
                
                if st.button("🚀 בנה גנט לפי תקציב", use_container_width=True):
                    with st.spinner("בונה גנט..."):
                        result = search_system.build_gantt_by_budget(budget, selected_locations if selected_locations else None)
                        
                        if isinstance(result, tuple):
                            text, table, images = result
                            st.success("✅ גנט נבנה בהצלחה!")
                            st.markdown(text)
                            
                            df_display = pd.DataFrame(table)
                            st.dataframe(df_display, use_container_width=True)
                            
                            st.session_state['last_gantt'] = {
                                'title': f'גנט פרסום - תקציב {budget:,.0f} ש״ח',
                                'table': table,
                                'type': 'budget'
                            }
                            
                            if images:
                                st.markdown("### 🖼️ תמונות האלמנטים")
                                cols = st.columns(min(3, len(images)))
                                for i, (item_code, image_path) in enumerate(images):
                                    with cols[i % 3]:
                                        search_system.display_image(image_path)
                                        st.caption(f"מק״ט: {item_code}")
                        else:
                            st.error(result)
            
            elif gantt_type == "גנט לפי סוג קמפיין":
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    campaign_type = st.selectbox("🎯 בחר סוג קמפיין:", ["דיגיטלי", "פרינט", "משולב"])
                    
                    use_budget = st.checkbox("💰 הגבל לפי תקציב")
                    
                    if use_budget:
                        budget_limit = st.number_input("תקציב מקסימלי (ש״ח)", min_value=0, value=30000, step=1000)
                    else:
                        budget_limit = None
                
                with col2:
                    if 'location' in search_system.columns_map:
                        location_col = search_system.columns_map['location']
                        all_locations = search_system.df[location_col].unique()
                        selected_locations_type = st.multiselect("🗺️ בחר מתחמים (אופציונלי)", all_locations, key="locations_by_type")
                    else:
                        selected_locations_type = None
                
                if st.button("🚀 בנה גנט לפי סוג", use_container_width=True):
                    with st.spinner("בונה גנט..."):
                        result = search_system.build_gantt_by_campaign_type(
                            campaign_type,
                            budget_limit if use_budget else None,
                            selected_locations_type if selected_locations_type else None
                        )
                        
                        if isinstance(result, tuple):
                            text, table, images = result
                            st.success("✅ גנט נבנה בהצלחה!")
                            st.markdown(text)
                            
                            df_display = pd.DataFrame(table)
                            st.dataframe(df_display, use_container_width=True)
                            
                            budget_text = f" - תקציב {budget_limit:,.0f} ש״ח" if use_budget and budget_limit else ""
                            locations_text = f" - {len(selected_locations_type)} מתחמים" if selected_locations_type else ""
                            st.session_state['last_gantt'] = {
                                'title': f'גנט פרסום - {campaign_type}{budget_text}{locations_text}',
                                'table': table,
                                'type': f'campaign_type_{campaign_type}'
                            }
                            
                            if images:
                                st.markdown("### 🖼️ תמונות האלמנטים")
                                cols = st.columns(min(3, len(images)))
                                for i, (item_code, image_path) in enumerate(images):
                                    with cols[i % 3]:
                                        search_system.display_image(image_path)
                                        st.caption(f"מק״ט: {item_code}")
                        else:
                            st.error(result)
    
    with tab3:
        if 'last_gantt' in st.session_state:
            gantt_data = st.session_state['last_gantt']
            
            st.info(f"📋 נתונים זמינים ליצוא: {gantt_data['title']}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📊 גרסה מלאה")
                
                if st.button("📊 הורד Excel מלא", key="excel_full"):
                    with st.spinner("יוצר קובץ Excel..."):
                        try:
                            export_buffer = search_system.create_excel_export(
                                gantt_data['table'], gantt_data['title'], include_price=True
                            )
                            
                            st.download_button(
                                label="💾 שמור Excel מלא",
                                data=export_buffer.getvalue(),
                                file_name=f"gantt_full_{gantt_data['type']}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                            st.success("✅ קובץ Excel מלא מוכן!")
                        except Exception as e:
                            st.error(f"❌ שגיאה: {e}")
                
                if st.button("📄 הורד PDF מלא", key="pdf_full"):
                    with st.spinner("יוצר PDF..."):
                        try:
                            pdf_buffer = search_system.create_pdf_export(
                                gantt_data['table'], gantt_data['title'], include_price=True
                            )
                            
                            st.download_button(
                                label="💾 שמור PDF מלא",
                                data=pdf_buffer.getvalue(),
                                file_name=f"gantt_full_{gantt_data['type']}.pdf",
                                mime="application/pdf"
                            )
                            st.success("✅ קובץ PDF מלא מוכן!")
                        except Exception as e:
                            st.error(f"❌ שגיאה: {e}")
            
            with col2:
                st.subheader("👥 גרסת לקוח")
                
                if st.button("📊 הורד Excel מקוצר", key="excel_short"):
                    with st.spinner("יוצר קובץ Excel..."):
                        try:
                            export_buffer = search_system.create_excel_export(
                                gantt_data['table'], gantt_data['title'], include_price=False
                            )
                            
                            st.download_button(
                                label="💾 שמור Excel מקוצר",
                                data=export_buffer.getvalue(),
                                file_name=f"gantt_client_{gantt_data['type']}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                            st.success("✅ קובץ Excel מקוצר מוכן!")
                        except Exception as e:
                            st.error(f"❌ שגיאה: {e}")
                
                if st.button("📄 הורד PDF מקוצר", key="pdf_short"):
                    with st.spinner("יוצר PDF..."):
                        try:
                            pdf_buffer = search_system.create_pdf_export(
                                gantt_data['table'], gantt_data['title'], include_price=False
                            )
                            
                            st.download_button(
                                label="💾 שמור PDF מקוצר",
                                data=pdf_buffer.getvalue(),
                                file_name=f"gantt_client_{gantt_data['type']}.pdf",
                                mime="application/pdf"
                            )
                            st.success("✅ קובץ PDF מקוצר מוכן!")
                        except Exception as e:
                            st.error(f"❌ שגיאה: {e}")
            
            st.markdown("### 👁️ תצוגה מקדימה")
            preview_df = pd.DataFrame(gantt_data['table'])
            
            preview_no_price = preview_df.copy()
            columns_to_remove = ['מק"ט', 'מחיר מכירה']
            for col in columns_to_remove:
                if col in preview_no_price.columns:
                    preview_no_price = preview_no_price.drop(columns=[col])
            
            tab_full, tab_client = st.tabs(["📊 גרסה מלאה", "👥 גרסת לקוח"])
            
            with tab_full:
                st.dataframe(preview_df, use_container_width=True)
            
            with tab_client:
                st.dataframe(preview_no_price, use_container_width=True)
        
        else:
            st.info("📋 צור גנט כדי לייצא נתונים")

if __name__ == "__main__":
    main()
