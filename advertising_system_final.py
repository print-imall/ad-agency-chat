import os
import sys
import pandas as pd
import json
import re
import random
from datetime import datetime

class AdvertisingSystem:
    def __init__(self):
        self.df = None
        self.columns_map = {}
        self.image_index = {}

    def load_data(self, file_path):
        if not os.path.exists(file_path):
            print(f"קובץ {file_path} לא נמצא")
            return False
        try:
            if file_path.endswith(".csv"):
                self.df = pd.read_csv(file_path)
            elif file_path.endswith(".xlsx"):
                self.df = pd.read_excel(file_path)
            else:
                print("פורמט קובץ לא נתמך")
                return False
            return True
        except Exception as e:
            print("שגיאה בטעינת נתונים:", e)
            return False

    def set_columns_map(self, mapping_dict):
        self.columns_map = mapping_dict

    def add_dropbox_image(self, item_code, dropbox_url):
        if "dl=0" in dropbox_url:
            direct_url = dropbox_url.replace("dl=0", "dl=1")
        else:
            direct_url = dropbox_url

        self.image_index[str(item_code).strip()] = direct_url
        return True

    def load_dropbox_folder(self, folder_path, token, code_prefix="item"):
        """
        טוען את כל התמונות מתוך תיקייה בדרופבוקס ושומר ב-image_index.
        folder_path - הנתיב לתיקייה בדרופבוקס (למשל "/MyImages")
        token - מפתח הגישה (Access Token)
        code_prefix - קידומת למספרי פריטים (ברירת מחדל: "item")
        """
        import dropbox
        dbx = dropbox.Dropbox(token)
        res = dbx.files_list_folder(folder_path)

        count = 0
        for entry in res.entries:
            if isinstance(entry, dropbox.files.FileMetadata):
                link = dbx.files_get_temporary_link(entry.path_lower).link
                self.add_dropbox_image(f"{code_prefix}_{count+1}", link)
                count += 1

        return count
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
                        score += 1
                        matching_details.append((field_name, part))
                        found = True
                        matched_parts += 1
                        break
                
                if not found:
                    score -= 0.5
            
            if matched_parts == len(query_parts) and score > best_score:
                best_score = score
                best_match = row
        
        if best_match is not None:
            return best_match.to_dict()
        else:
            return "לא נמצאו תוצאות מתאימות"
    
    def split_query(self, query):
        return [part.strip() for part in query.split() if part.strip()]
    
    def get_image(self, item_code):
        return self.image_index.get(str(item_code).strip(), None)

    def export_results(self, results, output_file="results.json"):
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print("שגיאה ביצוא:", e)
            return False
            def main():
    system = AdvertisingSystem()
    
    # דוגמה לטעינת נתונים
    data_loaded = system.load_data("data.xlsx")
    if not data_loaded:
        print("לא נטענו נתונים, בדוק את הנתיב לקובץ")
        return
    
    # מיפוי עמודות
    mapping = {
        "קוד פריט": "item_code",
        "תיאור": "description",
        "מחיר": "price"
    }
    system.set_columns_map(mapping)
    
    # טעינת תמונות מדרופבוקס (קובץ בודד/קישור ישיר)
    # system.add_dropbox_image("123", "https://www.dropbox.com/s/abc123/example.jpg?dl=0")
    
    # טעינת כל התמונות מתיקייה בדרופבוקס
    # כדי להשתמש בזה צריך להכניס Access Token תקף
    # token = "YOUR_ACCESS_TOKEN"
    # folder_path = "/MyImages"
    # num_loaded = system.load_dropbox_folder(folder_path, token)
    # print("נטענו", num_loaded, "תמונות מדרופבוקס")
    
    # דוגמה לחיפוש
    query = "שולחן עץ"
    result = system.smart_search(query)
    print("תוצאה לחיפוש:", result)
    
    # דוגמה לקבלת תמונה לפי קוד פריט
    # image_url = system.get_image("123")
    # print("לינק לתמונה:", image_url)

if __name__ == "__main__":
    main()
