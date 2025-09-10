import streamlit as st
import pandas as pd
import os
import requests
from PIL import Image
from pathlib import Path
import re
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import tempfile

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
    
    .success-banner {
        background: linear-gradient(90deg, #56ab2f 0%, #a8e6cf 100%);
        padding: 1rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin: 1rem 0;
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)

class AutomatedAdvertisingSystem:
    def __init__(self):
        self.df = None
        self.image_index = {}
        self.columns_map = {}
        self.excel_url = "https://github.com/print-imall/ad-agency-chat/raw/main/campaigns_data.xlsx"
        
        # תמונות ידועות
        self.known_images = {
            "11090111": "https://www.dropbox.com/scl/fi/lnklorrhl6gtovetf5m92/11090111.jpg?rlkey=o4wcjsdtzd4rqzep1i21lvfkk&st=whqr2eod&dl=1"
        }
        
        # אתחול התמונות
        self.image_index.update(self.known_images)
        
    def auto_load_data(self):
        """טעינה אוטומטית של נתוני האקסל מ-GitHub"""
        try:
            with st.spinner("🔄 טוען נתונים מהמערכת..."):
                response = requests.get(self.excel_url, timeout=30)
                response.raise_for_status()
                
                excel_buffer = BytesIO(response.content)
                self.df = pd.read_excel(excel_buffer, engine='openpyxl')
                self.df = self.clean_data()
                self.create_column_mapping()
                
                st.success("✅ נתונים נטענו בהצלחה מהמערכת!")
                return True
                
        except requests.exceptions.RequestException as e:
            st.error(f"❌ שגיאה בהורדת קובץ הנתונים: {e}")
            return False
        except Exception as e:
            st.error(f"❌ שגיאה בטעינת הנתונים: {e}")
            return False
    
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
            
            if len(columns) >= 10:
                self.columns_map['campaign'] = columns[9]

    def index_images(self, image_folder):
        if not os.path.exists(image_folder):
            st.warning(f"תיקיית התמונות לא נמצאה: {image_folder}")
            return
        
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        local_images = {}
        
        for file_path in Path(image_folder).glob('*'):
            if file_path.suffix.lower() in image_extensions:
                item_code = file_path.stem
                local_images[item_code] = str(file_path)
        
        self.image_index.update(local_images)
        st.success(f"נמצאו {len(local_images)} תמונות מקומיות")

    def add_dropbox_image(self, item_code, dropbox_url):
        """הוספת תמונה מדרופבוקס"""
        # המרה לקישור ישיר
        if "dl=0" in dropbox_url:
            direct_url = dropbox_url.replace("dl=0", "dl=1")
        else:
            direct_url = dropbox_url
        
        self.image_index[str(item_code).strip()] = direct_url
        return True

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
            'width': 'רוחב',
            'campaign': 'קמפיין'
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

    def display_image(self, image_path_or_url, caption=None):
        try:
            if isinstance(image_path_or_url, str) and image_path_or_url.startswith('http'):
                response = requests.get(image_path_or_url, timeout=10)
                if response.status_code == 200:
                    image = Image.open(BytesIO(response.content))
                    st.image(image, use_container_width=True, caption=caption)
                    return True
                else:
                    st.warning(f"לא ניתן לטעון תמונה מ: {image_path_or_url}")
                    return False
            else:
                image = Image.open(image_path_or_url)
                st.image(image, use_container_width=True, caption=caption)
                return True
        except Exception as e:
            st.warning(f"לא ניתן להציג תמונה: {e}")
            return False

def main():
    st.set_page_config(
        page_title="מערכת פרסום מתקדמת - אוטומטית", 
        page_icon="🚀", 
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    apply_custom_css()
    
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1 class="floating">🚀 מערכת פרסום אוטומטית</h1>
        <p style="font-size: 1.2rem; color: #667eea; font-weight: 500;">
            מערכת חכמה לחיפוש, בניית גנט ונידול קמפיינים פרסומיים
        </p>
        <div class="success-banner">
            ✨ חדש! הנתונים נטענים אוטומטית מהמערכת - אין צורך להעלות קבצים!
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if 'auto_system' not in st.session_state:
        st.session_state.auto_system = AutomatedAdvertisingSystem()
    
    system = st.session_state.auto_system
    
    if system.df is None:
        with st.spinner("🔄 מאתחל מערכת ונטען נתונים..."):
            if system.auto_load_data():
                st.balloons()
                st.markdown("""
                <div class="success-banner">
                    ✅ המערכת הותחלה בהצלחה! הנתונים נטענו מה-GitHub
                </div>
                """, unsafe_allow_html=True)
    
    with st.sidebar:
        st.markdown("### 🔄 בקרת מערכת")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 רענן נתונים", use_container_width=True):
                with st.spinner("מרענן נתונים
