import os
import sys
import json
import re
import random
from datetime import datetime

import pandas as pd

# אופציונלי: only import dropbox when using the Dropbox functions
# pip install dropbox

class AdvertisingSystem:
    def __init__(self):
        # DataFrame with your items
        self.df = None
        # מיפוי בין שמות שדות לעמודות ב-DataFrame
        self.columns_map = {}
        # מילון שממפה קוד פריט -> לינק לתמונה (direct link / temporary link)
        self.image_index = {}

    # ---------- data load / mapping ----------
    def load_data(self, file_path):
        """
        טוען קובץ CSV או XLSX ל-DataFrame (self.df).
        מחזיר True אם טעון בהצלחה, False אחרת.
        """
        if not os.path.exists(file_path):
            print(f"קובץ {file_path} לא נמצא")
            return False
        try:
            if file_path.lower().endswith(".csv"):
                self.df = pd.read_csv(file_path)
            elif file_path.lower().endswith((".xls", ".xlsx")):
                self.df = pd.read_excel(file_path)
            else:
                print("פורמט קובץ לא נתמך (תומך ב: .csv, .xls, .xlsx)")
                return False
            return True
        except Exception as e:
            print("שגיאה בטעינת נתונים:", e)
            return False

    def set_columns_map(self, mapping_dict):
        """
        קבלת מיפוי בין שמות שדות (לוגיים) לשמות העמודות ב-DataFrame.
        דוגמה: {"קוד פריט": "item_code", "תיאור": "description"}
        """
        self.columns_map = mapping_dict

    # ---------- image index helpers ----------
    def add_dropbox_image(self, item_code, dropbox_url):
        """
        מקבל URL ל־Dropbox (קישור ישיר או dl=0) ומשמור ב-image_index.
        לא עושה שאילתת API — אם מדובר בקישור ישיר לקובץ זה עובד.
        """
        if not dropbox_url:
            return False

        # אם זה לינק עם dl=0 נחליף ל-dl=1 כדי לקבל קישור ישיר (במקרים שמתאים)
        try:
            if "dl=0" in dropbox_url:
                direct_url = dropbox_url.replace("dl=0", "dl=1")
            else:
                direct_url = dropbox_url
            self.image_index[str(item_code).strip()] = direct_url
            return True
        except Exception:
            return False

    def auto_load_dropbox_images(self, code_column="item_code", url_column="dropbox_url"):
        """
        טוען אוטומטית מה-DataFrame (self.df) זוגות קוד-לינק.
        מצפה שה-DataFrame יכיל עמודה עם קוד הפריט ועמודה עם הקישור ל-Dropbox.
        מחזיר את מספר הפריטים שנוספו ל-image_index.
        """
        if self.df is None:
            return 0

        if code_column not in self.df.columns or url_column not in self.df.columns:
            return 0

        count = 0
        for _, row in self.df.iterrows():
            item_code = row.get(code_column)
            dropbox_url = row.get(url_column)
            if pd.isna(item_code) or pd.isna(dropbox_url):
                continue
            dropbox_url = str(dropbox_url).strip()
            if not dropbox_url:
                continue
            added = self.add_dropbox_image(item_code, dropbox_url)
            if added:
                count += 1
        return count

    def load_dropbox_folder(self, folder_path, token, code_prefix="item"):
        """
        טוען את כל הקבצים (תמונות) מתוך תיקייה בדרופבוקס בעזרת ה-Dropbox API.
        מחזיר את מספר התמונות שנוספו ל-image_index.

        פרמטרים:
        - folder_path: הנתיב בתיקיית Dropbox (לדוגמה "/MyImages")
        - token: Access Token של ה־Dropbox app
        - code_prefix: קידומת לשם הפריטים (ברירת מחדל "item"), ייווצרו קודים כמו item_1, item_2...
        """
        try:
            import dropbox
        except Exception as e:
            raise ImportError("חבילה dropbox לא מותקנת. הרץ: pip install dropbox") from e

        dbx = dropbox.Dropbox(token)
        count = 0
        cursor = None

        try:
            # התחלת קריאה לרשימת תיקייה
            res = dbx.files_list_folder(folder_path)
        except dropbox.exceptions.ApiError as e:
            # ייתכן שהתיקייה לא קיימת או שאין הרשאה
            return 0

        # helper function to process entries
        def _process_entries(entries, start_index):
            local_count = 0
            for entry in entries:
                # רק קבצים (לא תיקיות)
                if isinstance(entry, dropbox.files.FileMetadata):
                    # סינון סיומות תמונה מקובלות
                    _, ext = os.path.splitext(entry.name.lower())
                    if ext in [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"]:
                        try:
                            tmp_link_res = dbx.files_get_temporary_link(entry.path_lower)
                            tmp_link = tmp_link_res.link
                            code = f"{code_prefix}_{start_index + local_count + 1}"
                            # שמירת הלינק
                            self.image_index[code] = tmp_link
                            local_count += 1
                        except Exception:
                            # מעבר קובץ בעייתי — נדלג עליו
                            continue
            return local_count

        # process first page
        count += _process_entries(res.entries, count)

        # pagination אם יש עוד תוצאות
        while getattr(res, "has_more", False):
            try:
                res = dbx.files_list_folder_continue(res.cursor)
                count += _process_entries(res.entries, count)
            except Exception:
                break

        return count

    # ---------- smart search ----------
    def smart_search(self, query):
        """
        חיפוש חכם ב־DataFrame לפי מחרוזת חיפוש.
        מחזיר את ה-row (כמילון) שהכי מתאים לפי מיפוי ה-columns_map.
        אם לא נתמלאה DataFrame יחזיר הודעה מתאימה.
        """
        if self.df is None:
            return "לא נטענו נתונים עדיין"

        query_clean = str(query).strip()
        if not query_clean:
            return "שאילתה ריקה"

        query_parts = self.split_query(query_clean)

        best_match = None
        best_score = float("-inf")

        # עבור כל שורה נבצע בדיקת התאמה
        for idx, row in self.df.iterrows():
            score = 0
            matched_parts = 0

            for part in query_parts:
                part_lower = part.lower()
                found = False

                for field_name, col_name in self.columns_map.items():
                    # אם העמודה לא קיימת נתעלם
                    if col_name not in row:
                        continue
                    field_value = str(row[col_name]).lower()
                    if part_lower in field_value:
                        score += 1  # נקודה לכל מילה שנמצאה
                        found = True
                        matched_parts += 1
                        break

                if not found:
                    # מענישים קלות מילים שלא נמצאו
                    score -= 0.25

            # דרישת התאמה מלאה לכל חלקי השאילתה תעניק עדיפות
            if matched_parts == len(query_parts) and score > best_score:
                best_score = score
                best_match = row

        if best_match is not None:
            return best_match.to_dict()
        else:
            return "לא נמצאו תוצאות מתאימות"

    def split_query(self, query):
        """
        מפרק את השאילתה למילים (פשוט לפי רווחים, ניתן לשכלל)
        """
        if not isinstance(query, str):
            query = str(query)
        parts = [part.strip() for part in query.split() if part.strip()]
        return parts

    # ---------- utilities ----------
    def get_image(self, item_code):
        """
        מחזיר לינק לתמונה לפי קוד פריט אם קיים, אחרת None
        """
        return self.image_index.get(str(item_code).strip(), None)

    def export_results(self, results, output_file="results.json"):
        """
        מייצא תוצאות לקובץ JSON
        """
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print("שגיאה ביצוא:", e)
            return False

# ---------- main / דוגמה לשימוש ----------
def main():
    system = AdvertisingSystem()

    # דוגמה לטעינת נתונים
    data_path = "data.xlsx"  # שנה לפי הצורך
    data_loaded = system.load_data(data_path)
    if not data_loaded:
        print("לא נטענו נתונים, בדוק את הנתיב לקובץ")
        return

    # מיפוי עמודות (התאם לשמות העמודות בקובץ שלך)
    mapping = {
        "קוד פריט": "item_code",
        "תיאור": "description",
        "מחיר": "price"
    }
    system.set_columns_map(mapping)

    # דוגמה: טעינת לינקים ישירות מ-DataFrame (אם יש לך עמודת dropbox_url)
    # num_from_df = system.auto_load_dropbox_images(code_column="item_code", url_column="dropbox_url")
    # print("נטענו מה-DataFrame:", num_from_df)

    # דוגמה: טעינת כל התמונות מתיקייה בדרופבוקס (דורש Access Token תקף)
    # token = "YOUR_ACCESS_TOKEN"
    # folder_path = "/MyImages"
    # num_loaded = system.load_dropbox_folder(folder_path, token)
    # print("נטענו", num_loaded, "תמונות מדרופבוקס")

    # דוגמה לחיפוש
    query = "שולחן עץ"
    result = system.smart_search(query)
    print("תוצאה לחיפוש:", result)

    # דוגמה לקבלת תמונה לפי קוד פריט
    # image_url = system.get_image("item_1")
    # print("לינק לתמונה:", image_url)

if __name__ == "__main__":
    main()
