import os
import dropbox

class AdvertisingSystem:
    def __init__(self, dropbox_token: str):
        self.dbx = dropbox.Dropbox(dropbox_token)

    def list_images_from_dropbox_folder(self, folder_path: str):
        """
        מחזיר רשימת קישורים זמניים לכל התמונות בתיקייה בדרופבוקס.
        תומך בקבצי JPG, PNG, JPEG בלבד.
        """
        try:
            result = self.dbx.files_list_folder(folder_path)
            image_links = []

            for entry in result.entries:
                if isinstance(entry, dropbox.files.FileMetadata):
                    if entry.name.lower().endswith(('.png', '.jpg', '.jpeg')):
                        link = self.dbx.files_get_temporary_link(entry.path_lower)
                        image_links.append(link.link)

            return image_links

        except Exception as e:
            print(f"Error accessing Dropbox folder: {e}")
            return []

    def download_image_from_dropbox(self, file_path: str, local_path: str):
        """מוריד קובץ בודד מדרופבוקס לנתיב מקומי"""
        try:
            self.dbx.files_download_to_file(local_path, file_path)
            return True
        except Exception as e:
            print(f"Error downloading file {file_path}: {e}")
            return False

    def smart_search(self, query: str):
        """
        חיפוש חכם - כרגע דמה (מחזיר טקסט מותאם לשאילתה)
        כאן תוכל להרחיב בעתיד לחיפוש אמיתי במסד נתונים או API
        """
        return f"Results for query: {query}"


if __name__ == "__main__":
    # דוגמה להפעלה (שים כאן את הטוקן האישי שלך מדרופבוקס)
    DROPBOX_TOKEN = os.getenv("DROPBOX_TOKEN", "YOUR_DROPBOX_TOKEN")
    system = AdvertisingSystem(DROPBOX_TOKEN)

    # דוגמה: שליפת כל התמונות מתיקייה בדרופבוקס
    folder = "/public_images"  # שנה לנתיב אצלך בדרופבוקס
    images = system.list_images_from_dropbox_folder(folder)

    print(f"Found {len(images)} images in folder '{folder}'")
    for img in images:
        print(img)
