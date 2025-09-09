import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# URLs for data and images
GITHUB_DATA_URL = "https://raw.githubusercontent.com/print-imall/ad-agency-chat/main/campaigns_data.xlsx"

class AdvertisingSystem:
    def __init__(self):
        self.df = None
        self.columns_map = {}
        self.load_data_from_github()
    
    def load_data_from_github(self):
        """טוען נתונים מGitHub"""
        try:
            with st.spinner("טוען נתונים מהענן..."):
                response = requests.get(GITHUB_DATA_URL)
                response.raise_for_status()
                
                excel_data = BytesIO(response.content)
                self.df = pd.read_excel(excel_data, engine='openpyxl')
                
                # ניקוי נתונים
                for col in self.df.columns:
                    self.df[col] = self.df[col].astype(str).str.strip()
                self.df = self.df.dropna(how='all')
                
                # יצירת מיפוי עמודות
                columns = list(self.df.columns)
                if len(columns) >= 10:
                    self.columns_map = {
                        'location': columns[0],
                        'item_code': columns[1], 
                        'platform': columns[2],
                        'price': columns[3],
                        'visitors': columns[4],
                        'height': columns[5],
                        'width': columns[6],
                        'height2': columns[7],
                        'width2': columns[8],
                        'campaign': columns[9]
                    }
                
                st.success(f"נטענו {len(self.df)} פריטים מהענן")
                return True
                
        except Exception as e:
            st.error(f"שגיאה בטעינת נתונים: {e}")
            return False
    
    def build_gantt_by_campaign_type(self, campaign_type, budget=None, target_locations=None):
        """בניית גאנט לפי סוג קמפיין"""
        if self.df is None:
            return "❌ לא נטענו נתונים"
        
        if 'campaign' not in self.columns_map:
            return "❌ לא נמצאה עמודת קמפיין"
        
        campaign_col = self.columns_map['campaign']
        
        # סינון לפי סוג קמפיין
        if campaign_type.lower() == "דיגיטלי":
            mask = self.df[campaign_col].str.strip().str.lower() == 'דיגיטלי'
        elif campaign_type.lower() == "פרינט":
            mask = self.df[campaign_col].str.strip().str.lower() == 'פרינט'
        else:
            return f"❌ סוג קמפיין לא מוכר: {campaign_type}"
        
        df_filtered = self.df[mask].copy()
        
        if df_filtered.empty:
            return f"❌ לא נמצאו אלמנטים מסוג {campaign_type}"
        
        # סינון לפי מתחמים
        if target_locations:
            location_col = self.columns_map['location']
            df_filtered = df_filtered[df_filtered[location_col].str.contains('|'.join(target_locations), case=False, na=False)]
        
        # חישוב מחירים
        price_col = self.columns_map['price']
        df_filtered['price_numeric'] = pd.to_numeric(
            df_filtered[price_col].astype(str).str.replace(r'[^\d.]', '', regex=True),
            errors='coerce'
        ).fillna(0)
        
        # סינון לפי תקציב
        if budget:
            budget = float(budget)
            df_sorted = df_filtered.sort_values('price_numeric')
            
            selected_items = []
            current_total = 0
            
            for _, row in df_sorted.iterrows():
                item_price = row['price_numeric']
                if current_total + item_price <= budget:
                    selected_items.append(row)
                    current_total += item_price
                    if current_total >= budget * 0.95:
                        break
            
            if not selected_items:
                return f"❌ לא נמצאו אלמנטים מתאימים לתקציב {budget:,.0f} ש״ח"
            
            total_cost = sum(item['price_numeric'] for item in selected_items)
        else:
            selected_items = df_filtered.to_dict('records')
            total_cost = df_filtered['price_numeric'].sum()
        
        # יצירת טבלה לתצוגה
        table_data = []
        for i, item in enumerate(selected_items, 1):
            table_row = {
                'מס\'': i,
                'מק"ט': item[self.columns_map['item_code']],
                'מתחם': item[self.columns_map['location']],
                'פלטפורמה': item[self.columns_map['platform']],
                'קמפיין': item[self.columns_map['campaign']],
                'מחיר': f"{item['price_numeric']:,.0f} ש״ח",
                'מבקרים': f"{float(item[self.columns_map['visitors']]):,.0f}",
            }
            table_data.append(table_row)
        
        # יצירת סיכום
        result_text = f"📊 **גאנט {campaign_type}**\n\n"
        if budget:
            result_text += f"💰 תקציב: {budget:,.0f} ש״ח\n"
            result_text += f"💵 עלות: {total_cost:,.0f} ש״ח\n"
            result_text += f"📈 ניצול: {(total_cost/budget)*100:.1f}%\n"
        else:
            result_text += f"💵 עלות כוללת: {total_cost:,.0f} ש״ח\n"
        result_text += f"📋 פריטים: {len(selected_items)}\n"
        
        return result_text, table_data

def main():
    st.set_page_config(
        page_title="מערכת פרסום", 
        page_icon="🚀", 
        layout="wide"
    )
    
    st.title("🚀 מערכת פרסום מתקדמת")
    st.markdown("### נתונים נטענים אוטומטית מהענן")
    
    # יצירת מערכת
    if 'system' not in st.session_state:
        st.session_state.system = AdvertisingSystem()
    
    system = st.session_state.system
    
    # סייד בר עם סטטיסטיקות
    with st.sidebar:
        st.header("📊 סטטיסטיקות")
        if system.df is not None:
            st.metric("פריטים", len(system.df))
            
            if 'campaign' in system.columns_map:
                campaign_col = system.columns_map['campaign']
                campaign_counts = system.df[campaign_col].value_counts()
                st.write("פילוח קמפיינים:")
                for campaign_type, count in campaign_counts.items():
                    st.write(f"• {campaign_type}: {count}")
        
        if st.button("🔄 רענן נתונים"):
            system.load_data_from_github()
            st.rerun()
    
    # בניית גאנט
    if system.df is not None:
        st.header("📊 בניית גאנט")
        
        col1, col2 = st.columns(2)
        
        with col1:
            campaign_type = st.selectbox("סוג קמפיין:", ["דיגיטלי", "פרינט"])
            use_budget = st.checkbox("הגבל לפי תקציב")
            
            if use_budget:
                budget = st.number_input("תקציב (ש״ח):", min_value=0, value=30000, step=1000)
            else:
                budget = None
        
        with col2:
            if 'location' in system.columns_map:
                location_col = system.columns_map['location']
                all_locations = system.df[location_col].unique()
                selected_locations = st.multiselect("מתחמים (אופציונלי):", all_locations)
            else:
                selected_locations = None
        
        if st.button("🚀 בנה גאנט", use_container_width=True):
            result = system.build_gantt_by_campaign_type(
                campaign_type, 
                budget, 
                selected_locations if selected_locations else None
            )
            
            if isinstance(result, tuple):
                text, table = result
                st.success("✅ גאנט נבנה בהצלחה!")
                st.markdown(text)
                
                df_display = pd.DataFrame(table)
                st.dataframe(df_display, use_container_width=True)
            else:
                st.error(result)
    else:
        st.error("לא ניתן לטעון נתונים מהענן")

if __name__ == "__main__":
    main()
