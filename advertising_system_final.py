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

class SimplifiedAdvertisingSystem:
    def __init__(self):
        self.df = None
        self.image_index = {}
        self.columns_map = {}
        self.excel_url = "https://github.com/print-imall/ad-agency-chat/raw/main/campaigns_data.xlsx"
        
        # תמונת דוגמה שעובדת
        self.image_index["11090111"] = "https://www.dropbox.com/scl/fi/lnklorrhl6gtovetf5m92/11090111.jpg?rlkey=o4wcjsdtzd4rqzep1i21lvfkk&st=whqr2eod&dl=1"
        
    def auto_load_data(self):
        try:
            response = requests.get(self.excel_url, timeout=30)
            response.raise_for_status()
            
            excel_buffer = BytesIO(response.content)
            self.df = pd.read_excel(excel_buffer, engine='openpyxl')
            self.df = self.clean_data()
            self.create_column_mapping()
            
            return True
                
        except Exception as e:
            st.error(f"שגיאה בטעינת נתונים: {e}")
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
            
            return "מטמון נוקה בהצלחה!"
        except Exception as e:
            return f"שגיאה בניקוי מטמון: {e}"

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

    def add_dropbox_image(self, item_code, dropbox_url):
        if "dl=0" in dropbox_url:
            direct_url = dropbox_url.replace("dl=0", "dl=1")
        else:
            direct_url = dropbox_url
        
        self.image_index[str(item_code).strip()] = direct_url
        return True

    def smart_search(self, query):
        if self.df is None:
            return "לא נטענו נתונים עדיין"
        
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
                        matching_details.append(f"'{part}' נמצא ב{hebrew_name}")
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
            return f"לא נמצאה התאמה עבור: {', '.join(query_parts)}"
        
        return self.format_result(best_match, query_clean)

    def build_gantt_by_budget(self, budget, target_locations=None):
        if self.df is None:
            return "לא נטענו נתונים עדיין"
        
        try:
            budget = float(budget)
        except:
            return "תקציב חייב להיות מספר"
        
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
            return f"לא נמצאו פריטים שמתאימים לתקציב {budget:,.0f} שח"
        
        return self.format_gantt_result(selected_items, current_total, budget, "תקציב")

    def build_gantt_by_campaign_type(self, campaign_type, budget=None, target_locations=None):
        if self.df is None:
            return "לא נטענו נתונים עדיין"
        
        if campaign_type.lower() == "דיגיטלי":
            keywords = ['פייסבוק', 'אינסטגרם', 'גוגל', 'דיגיטל', 'פריימלס', 'וויז']
        elif campaign_type.lower() == "פרינט":
            keywords = ['בילבורד', 'חוצות', 'עיתון', 'מודעה', 'פוסטר', 'שלט', 'מחסומים', 'טבעת']
        elif campaign_type.lower() == "משולב":
            keywords = ['פייסבוק', 'אינסטגרם', 'גוגל', 'דיגיטל', 'פריימלס', 'וויז', 'בילבורד', 'חוצות', 'עיתון', 'מודעה', 'פוסטר', 'שלט', 'מחסומים', 'טבעת']
        else:
            return f"סוג קמפיין לא מוכר: {campaign_type}"
        
        platform_col = self.columns_map['platform']
        df_filtered = self.df[
            self.df[platform_col].str.contains('|'.join(keywords), case=False, na=False)
        ]
        
        if target_locations and len(target_locations) > 0:
            location_col = self.columns_map['location']
            df_filtered = df_filtered[df_filtered[location_col].str.contains('|'.join(target_locations), case=False, na=False)]
        
        if df_filtered.empty:
            location_text = " במתחמים שנבחרו" if target_locations and len(target_locations) > 0 else ""
            return f"לא נמצאו פריטים מסוג {campaign_type}{location_text}"
        
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
                    location_text = " במתחמים שנבחרו" if target_locations and len(target_locations) > 0 else ""
                    return f"לא נמצאו פריטים מסוג {campaign_type} שמתאימים לתקציב {budget:,.0f} שח{location_text}"
                
                return self.format_gantt_result(selected_items, current_total, budget, f"{campaign_type} עם תקציב")
            except:
                pass
        
        selected_items = df_filtered.to_dict('records')
        total_cost = df_filtered['price_numeric'].sum()
        
        location_text = " במתחמים שנבחרו" if target_locations and len(target_locations) > 0 else ""
        return self.format_gantt_result(selected_items, total_cost, None, f"{campaign_type}{location_text}")

    def format_gantt_result(self, items, total_cost, budget, gantt_type):
        num_items = len(items)
        
        result_text = f"📊 **דוח גנט - {gantt_type}**\n\n"
        
        if budget:
            result_text += f"💰 **תקציב:** {budget:,.0f} שח\n"
            result_text += f"💵 **עלות כוללת:** {total_cost:,.0f} שח\n"
            result_text += f"📈 **ניצול תקציב:** {(total_cost/budget)*100:.1f}%\n"
        else:
            result_text += f"💵 **עלות כוללת:** {total_cost:,.0f} שח\n"
        
        result_text += f"📋 **מספר פריטים:** {num_items}\n\n"
        
        table_data = []
        images_to_show = []
        
        for i, item in enumerate(items, 1):
            table_row = {
                'מס': i,
                'מקט': item[self.columns_map['item_code']],
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
                columns_to_remove = ['מקט', 'מחיר מכירה']
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
                columns_to_remove = ['מקט', 'מחיר מכירה']
                for col in columns_to_remove:
                    if col in df.columns:
                        df = df.drop(columns=[col])
            
            table_values = [list(df.columns)]
            for _, row in df.iterrows():
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
        
        platform_patterns = ['פריימלס', 'פייסבוק', 'אינסטגרם', 'גוגל', 'מחסומים', 'טבעת']
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
            'item_code': 'מקט',
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
            'מקט': row[self.columns_map['item_code']],
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
                return f"{price_num:,.0f} שח"
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
        page_title="מערכת פרסום אוטומטית", 
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
            ✨ הנתונים נטענים אוטומטית מהמערכת - אין צורך להעלות קבצים!
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if 'system' not in st.session_state:
        st.session_state.system = SimplifiedAdvertisingSystem()
    
    system = st.session_state.system
    
    if system.df is None:
        with st.spinner("מאתחל מערכת וטוען נתונים..."):
            if system.auto_load_data():
                st.balloons()
                st.success("המערכת הותחלה בהצלחה!")
    
    with st.sidebar:
        st.markdown("### 🔄 בקרת מערכת")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 רענן נתונים", use_container_width=True):
                with st.spinner("מרענן נתונים..."):
                    if system.auto_load_data():
                        st.success("נתונים עודכנו!")
                        st.rerun()
        
        with col2:
            if st.button("🗑️ נקה מטמון", use_container_width=True):
                result = system.clear_cache()
                st.success(result)
                st.rerun()
        
        st.markdown("---")
        
        st.markdown("### 🔗 הוספת תמונות")
        
        with st.expander("💡 הוראות הוספת תמונות מדרופבוקס"):
            st.markdown("""
            **איך להוסיף תמונות מדרופבוקס:**
            1. היכנס לתיקיית התמונות בדרופבוקס
            2. לחץ על תמונה ובחר "שתף"
            3. העתק את הקישור
            4. הוסף את המקט והקישור במערכת למטה
            
            **חשוב:** וודא שהתמונות נקראות בדיוק כמו המקט (למשל: 11090111.jpg)
            """)
        
        col1, col2 = st.columns([1, 2])
        with col1:
            new_item_code = st.text_input("מקט:")
        with col2:
            new_image_url = st.text_input("קישור דרופבוקס:")
        
        if st.button("➕ הוסף תמונה", use_container_width=True) and new_item_code and new_image_url:
            if system.add_dropbox_image(new_item_code, new_image_url):
                st.success(f"✅ תמונה נוספה למקט {new_item_code}")
        
        st.markdown("### 📋 הוספה קבוצתית")
        with st.expander("הוספת מספר מקטים בבת אחת"):
            st.markdown("""
            **להוספה קבוצתית:**
            1. העתק רשימת מקטים (אחד בכל שורה)
            2. הדבק כאן למטה
            3. לחץ הוסף - תוכל להוסיף קישורים אחר כך
            """)
            
            bulk_codes = st.text_area("הדבק מקטים (אחד בכל שורה):", height=100)
            if st.button("הוסף מקטים", use_container_width=True) and bulk_codes:
                codes = [code.strip() for code in bulk_codes.split('\n') if code.strip()]
                added_count = 0
                for code in codes:
                    # הוסף placeholder למקט
                    system.image_index[code] = "placeholder"
                    added_count += 1
                
                if added_count > 0:
                    st.success(f"נוספו {added_count} מקטים. הוסף קישורי תמונות בעת הצורך.")
        
        if system.df is not None:
            st.markdown("---")
            st.markdown("### 📊 סטטיסטיקות")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"""
                <div class="metric-container">
                    <h3 style="color: #667eea; margin: 0;">📋</h3>
                    <h2 style="margin: 0.5rem 0;">{len(system.df):,}</h2>
                    <p style="margin: 0; color: #666;">פריטים</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="metric-container">
                    <h3 style="color: #764ba2; margin: 0;">🖼️</h3>
                    <h2 style="margin: 0.5rem 0;">{len(system.image_index):,}</h2>
                    <p style="margin: 0; color: #666;">תמונות</p>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            st.markdown("### 🎯 מידע על הנתונים")
            st.info(f"📅 נתונים עודכנו לאחרונה: {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')}")
            st.info("🌐 מקור: GitHub Repository")
            st.info("☁️ תמונות: Dropbox")
            
            if system.image_index:
                st.markdown("### 🖼️ תמונות זמינות")
                st.info(f"כרגע {len(system.image_index)} תמונה/ות זמינות במערכת")
                
                # הצג רק תמונות אמיתיות (לא placeholder)
                real_images = {k: v for k, v in system.image_index.items() if v != "placeholder"}
                
                if real_images:
                    sample_items = list(real_images.items())[:3]
                    cols = st.columns(min(3, len(sample_items)))
                    
                    for i, (item_code, image_url) in enumerate(sample_items):
                        with cols[i]:
                            try:
                                response = requests.get(image_url, timeout=5)
                                if response.status_code == 200:
                                    image = Image.open(BytesIO(response.content))
                                    st.image(image, caption=f"מקט: {item_code}", use_container_width=True)
                                else:
                                    st.warning(f"לא ניתן לטעון תמונה {item_code}")
                            except:
                                st.warning(f"שגיאה בטעינת תמונה {item_code}")
                else:
                    st.info("השתמש בטופס למעלה כדי להוסיף קישורי תמונות")
    
    tab1, tab2, tab3 = st.tabs(["🔍 חיפוש חכם", "📊 בניית גנט", "📄 ייצוא מתקדם"])
    
    with tab1:
        if system.df is None:
            st.error("❌ שגיאה בטעינת הנתונים. נסה לרענן את הדף.")
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
                            system.display_image(message['image'])
            
            user_input = st.chat_input("🔍 שאל שאלה או חפש משהו...")
            
            if user_input:
                st.session_state.history.append({'role': 'user', 'content': user_input})
                
                with st.spinner("🔍 מחפש..."):
                    result = system.smart_search(user_input)
                    
                    if isinstance(result, tuple):
                        text, table, image = result
                        msg = {'role': 'assistant', 'content': text, 'table': table}
                        if image:
                            msg['image'] = image
                        st.session_state.history.append(msg)
                    else:
                        st.session_state.history.append({'role': 'assistant', 'content': result})
                
                st.rerun()
    
    with tab2:
        if system.df is None:
            st.warning("❌ שגיאה בטעינת הנתונים")
        else:
            gantt_type = st.selectbox("בחר סוג גנט:", ["גנט לפי תקציב", "גנט לפי סוג קמפיין"])
            
            if gantt_type == "גנט לפי תקציב":
                col1, col2 = st.columns([2, 3])
                
                with col1:
                    budget = st.number_input("💰 תקציב (שח)", min_value=0, value=50000, step=1000)
                
                with col2:
                    if 'location' in system.columns_map:
                        location_col = system.columns_map['location']
                        all_locations = system.df[location_col].unique()
                        selected_locations = st.multiselect("🗺️ בחר מתחמים (אופציונלי)", all_locations)
                
                if st.button("🚀 בנה גנט לפי תקציב", use_container_width=True):
                    with st.spinner("בונה גנט..."):
                        result = system.build_gantt_by_budget(budget, selected_locations if selected_locations else None)
                        
                        if isinstance(result, tuple):
                            text, table, images = result
                            st.success("✅ גנט נבנה בהצלחה!")
                            st.markdown(text)
                            
                            df_display = pd.DataFrame(table)
                            st.dataframe(df_display, use_container_width=True)
                            
                            st.session_state['last_gantt'] = {
                                'title': f'גנט פרסום - תקציב {budget:,.0f} שח',
                                'table': table,
                                'type': 'budget'
                            }
                            
                            if images:
                                st.markdown("### 🖼️ תמונות האלמנטים")
                                cols = st.columns(min(3, len(images)))
                                for i, (item_code, image_path) in enumerate(images):
                                    with cols[i % 3]:
                                        system.display_image(image_path, f"מקט: {item_code}")
                        else:
                            st.error(result)
            
            elif gantt_type == "גנט לפי סוג קמפיין":
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    campaign_type = st.selectbox("🎯 בחר סוג קמפיין:", ["דיגיטלי", "פרינט", "משולב"])
                    
                    use_budget = st.checkbox("💰 הגבל לפי תקציב")
                    
                    if use_budget:
                        budget_limit = st.number_input("תקציב מקסימלי (שח)", min_value=0, value=30000, step=1000)
                    else:
                        budget_limit = None
                
                with col2:
                    if 'location' in system.columns_map:
                        location_col = system.columns_map['location']
                        all_locations = system.df[location_col].unique()
                        selected_locations_type = st.multiselect("🗺️ בחר מתחמים (אופציונלי)", all_locations, key="locations_by_type")
                    else:
                        selected_locations_type = None
                
                if st.button("🚀 בנה גנט לפי סוג", use_container_width=True):
                    with st.spinner("בונה גנט..."):
                        result = system.build_gantt_by_campaign_type(
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
                            
                            budget_text = f" - תקציב {budget_limit:,.0f} שח" if use_budget and budget_limit else ""
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
                                        system.display_image(image_path, f"מקט: {item_code}")
                        else:
                            st.error(result)
    
    with tab3:
        if 'last_gantt' in st.session_state:
            gantt_data = st.session_state['last_gantt']
            
            st.info(f"📋 נתונים זמינים לייצוא: {gantt_data['title']}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📊 גרסה מלאה")
                
                if st.button("📊 הורד Excel מלא", key="excel_full"):
                    with st.spinner("יוצר קובץ Excel..."):
                        try:
                            export_buffer = system.create_excel_export(
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
                            pdf_buffer = system.create_pdf_export(
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
                            export_buffer = system.create_excel_export(
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
                            pdf_buffer = system.create_pdf_export(
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
            columns_to_remove = ['מקט', 'מחיר מכירה']
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
