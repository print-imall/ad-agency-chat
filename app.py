import os
import streamlit as st
from advertising_system_final_full import AdvertisingSystem

# כותרת
st.set_page_config(page_title="Advertising System Chat", layout="wide")
st.title("📢 Advertising System - Chat Web App")

# הגדרת טוקן של דרופבוקס
dropbox_token = st.text_input("🔑 Dropbox Token", type="password", value=os.getenv("DROPBOX_TOKEN", ""))

# אם אין טוקן - נעצור
if not dropbox_token:
    st.warning("אנא הזן Dropbox Token כדי להתחיל.")
    st.stop()

# יצירת אובייקט מערכת
system = AdvertisingSystem(dropbox_token)

# בחירת תיקייה בדרופבוקס
folder = st.text_input("📂 נתיב תיקייה בדרופבוקס", value="/public_images")

# הצגת תמונות מהתיקייה
if st.button("📥 שלוף תמונות"):
    images = system.list_images_from_dropbox_folder(folder)
    if not images:
        st.error("❌ לא נמצאו תמונות בתיקייה.")
    else:
        st.success(f"נמצאו {len(images)} תמונות!")
        cols = st.columns(3)
        for i, img in enumerate(images):
            with cols[i % 3]:
                st.image(img, use_container_width=True)

st.markdown("---")

# תיבת צ'אט / חיפוש
st.subheader("💬 Smart Search")
query = st.text_input("הקלד שאילתה")

if st.button("🔍 חפש"):
    if query:
        result = system.smart_search(query)
        st.info(result)
    else:
        st.warning("אנא הקלד שאילתה לחיפוש.")
