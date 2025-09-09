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

import dropbox

DROPBOX_ACCESS_TOKEN = "sl.u.AF_9pP-d4lsknuqtOjvaLhGOcMUdtcCGZxkiWf13zhAr-BFwmyYvfMe5_xuuZ6KxChh2sQhnRrR4WlulxbPVg0hcEkyin0HPioiULZsQT4pLi8ctLu73yNVgyzEE0fjMGQ7yacV55DWWM7CNNOTxP7kOFsPXrVUK6d6HBbeS0W7qjxlPJvMb1ozOTy6lelXx7e-RtLEc9CJanLTf57haZ1oKFHXXMqPadLdrAvpfI5k0ss8qza-Bn9aTqeESjXfpN6Cjfd4YgK4z6KzzCwTMVsrFfHTu4z-MSalclNcshBmJ7bM7rvddG4ARN1aTAyCcmYZZcvD98rH1Tr7HoNyrsmxw-yV8IclG4o_sfabl5SRpfZttUkPiExMwycvut0GWHYylWdjddOozQWslY6_fTv0JfUDpGeop4W0hTLoGJ8BhJpW5pQDy8VavL6n31MIOHZk27iDoG6_kK9PbPN5jSvRpBwLS3TmBwOdkCApWeLCjlWduJ4lk486MAfsfXW2iivCkG8PXs1E8uNVGbr4M9jZctOsRIJO6-e0L9P5iNlm7Sn2Qf5uyWcaRdBkYTV2cNY6ubk5U0XgfllGuwYRGfHvOtnGZaNTtAOGvBcMNU3xRdAgCs8dB0wsf55Lr30I7qB4QeNW5e0WsgGOURcDhul40f1DX3K26zMi3Oa3I6X4S2-0ZrVtGClgc8vPyenNrooVvYEBZD8SQjGoBhXYNwchJaOAgFreFdU4mNGFaPyV5gmlGVeZ-0HH8_Mq0lqih6dWt80tiPdi15zi7L595s0g4KOAF9otte-VUiSCHavUB9TuU50kV3kOi8g7HOHHX4zYF-0lSeJko0Y7QJZaOKvb_PjAuJTTghhPNv_dNDzmN_Y9IixWdNrRzIygwDMG0LMCqFvNEbGfcB2q7azh64bzfgfvFRBjl3OT2zgqYRmBevbdWmN64l5ppA0SZrCT3SudYa9ez_Wx7AUM08TtnvoPVQJ0fRA2V-Jca5Xq3_3iuzQKpA45azqdsm0xt0GLQ3CdWimdQde1bwH4jSdbaaWH-wAqnKlJEl6MNx9X-ZFHGLmHs65woXWdt2jHzWoScW2ovU-yE6z5N_myZ6zvHu1pntbR8he5DuX2kP5ZEyd34Pt2Q-WhYFdwA044dQz5JkV4oYC8PS4wsw1jcFGNaxQ6bdl_ZJHudXVX1Selv2L7Tz4E6t5xSb0FdgofKb27l61H1icWLafg6cK0N2ytDie-Mh9EZIdmjeDAFleLNGdUnwon0Jw_XZvp7I5X5RKx4jX05c1ZxQ5Ucg31QTIrPgwQc"
DROPBOX_FOLDER_PATH = "/תמונות לפי מקט"  # שנה נתיב לפי הצורך

class DropboxImageFetcher:
    def __init__(self, access_token, folder_path):
        self.dbx = dropbox.Dropbox(access_token)
        self.folder_path = folder_path

    def get_image_files(self):
        result = self.dbx.files_list_folder(self.folder_path)
        image_files = []
        for entry in result.entries:
            if isinstance(entry, dropbox.files.FileMetadata):
                if entry.name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                    image_files.append(entry.path_lower)
        return image_files

    def download_image(self, file_path):
        _, response = self.dbx.files_download(file_path)
        return BytesIO(response.content)

    def get_image_link(self, file_path):
        try:
            link_metadata = self.dbx.sharing_create_shared_link_with_settings(file_path)
            return link_metadata.url.replace("?dl=0", "?raw=1")
        except Exception:
            links = self.dbx.sharing_list_shared_links(path=file_path).links
            if links:
                return links[0].url.replace("?dl=0", "?raw=1")
            return None

class FixedEnhancedSystem:
    def __init__(self):
        self.df = None
        self.image_index = {}
        self.columns_map = {}
        self.dropbox_images = None
        self.image_links = {}
        self.default_github_url = "https://raw.githubusercontent.com/print-imall/ad-agency-chat/main/campaigns_data.xlsx"
        # טעינה אוטומטית של התמונות מדרופבוקס
        self.index_images_from_dropbox()

    def index_images_from_dropbox(self):
        try:
            fetcher = DropboxImageFetcher(DROPBOX_ACCESS_TOKEN, DROPBOX_FOLDER_PATH)
            image_files = fetcher.get_image_files()
            self.image_index = {}
            self.image_links = {}
            for file_path in image_files:
                item_code = Path(file_path).stem
                self.image_index[item_code] = file_path
                link = fetcher.get_image_link(file_path)
                if link:
                    self.image_links[item_code] = link
            self.dropbox_images = fetcher
        except Exception as e:
            st.error(f"שגיאה בשליפת תמונות מדרופבוקס: {e}")

    def display_image(self, image_path, item_code=None):
        try:
            if self.dropbox_images and image_path.startswith('/'):
                image_data = self.dropbox_images.download_image(image_path)
                image = Image.open(image_data)
                st.image(image, use_container_width=True)
                if item_code and item_code in self.image_links:
                    st.markdown(f"[🔗 לינק לתמונה]({self.image_links[item_code]})")
            else:
                image = Image.open(image_path)
                st.image(image, use_container_width=True)
            return True
        except Exception as e:
            st.warning(f"לא ניתן להציג תמונה: {e}")
            return False

    def create_excel_export(self, table_data, title, include_price=True):
        buffer = BytesIO()
        if not table_data:
            df_empty = pd.DataFrame({"הודעה": ["אין נתונים להצגה"]})
            df_empty.to_excel(buffer, index=False, engine='openpyxl')
        else:
            df = pd.DataFrame(table_data)
            df['לינק תמונה'] = df['מק"ט'].map(self.image_links)
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
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            hebrew_font_loaded = False
            hebrew_fonts = [
                'C:/Windows/Fonts/arial.ttf',
                'C:/Windows/Fonts/calibri.ttf', 
                'C:/Windows/Fonts/tahoma.ttf',
                '/System/Library/Fonts/Arial.ttf',
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
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
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        hebrew_style = ParagraphStyle(
            'Hebrew',
            parent=styles['Normal'],
            fontName='HebrewFont',
            fontSize=12,
            alignment=2,
            wordWrap='RTL'
        )
        title_style = ParagraphStyle(
            'HebrewTitle',
            parent=styles['Heading1'],
            fontName='HebrewFont',
            fontSize=16,
            spaceAfter=30,
            alignment=1
        )
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 20))
        if not table_data:
            story.append(Paragraph("אין נתונים להצגה", hebrew_style))
        else:
            df = pd.DataFrame(table_data)
            df['לינק תמונה'] = df['מק"ט'].map(self.image_links)
            if not include_price:
                columns_to_remove = ['מק"ט', 'מחיר מכירה']
                for col in columns_to_remove:
                    if col in df.columns:
                        df = df.drop(columns=[col])
            table_values = []
            headers = list(df.columns)
            table_values.append(headers)
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

# === UI ===
def main():
    st.set_page_config(
        page_title="מערכת פרסום מתקדמת", 
        page_icon="🚀", 
        layout="wide",
        initial_sidebar_state="expanded"
    )
    # יצירת מערכת אם לא קיימת
    if 'enhanced_search' not in st.session_state:
        st.session_state.enhanced_search = FixedEnhancedSystem()
    search_system = st.session_state.enhanced_search
    # אין צורך בכפתור/הזנה לתמונות, התמונות כבר מוטענות
    # בשאר הקוד, בכל מקום בו מוצגת תמונה:
    # search_system.display_image(image_path, item_code)
    # ובייצוא: עמודת "לינק תמונה" תתווסף אוטומטית

if __name__ == "__main__":
    main()
