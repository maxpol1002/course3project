import db
from classes.File import File


class DailyReport:
    def __init__(self, report_id: int, user_id: int, report_name: str, report_desc: str, send_time: str,
                 files: list[File] or None):
        self.report_id = report_id
        self.user_id = user_id
        self.report_name = report_name
        self.report_desc = report_desc
        self.send_time = send_time
        self.files = files

    def create_report_text(self) -> str:
        data = (
            "==================================\n"
            f"Номер звіту: {self.report_id}\n"
            f"Відправник: {db.db_get_user_data(user_id=self.user_id)}\n"
            f"Назва: {self.report_name}\n"
            f"Текст звіту: {self.report_desc}\n"
            f"Час відправлення: {self.send_time}\n"
            "=================================="

        )

        return data

    def get_media(self) -> tuple or None:
        photos = []
        videos = []
        docs = []
        if self.files:
            for file in self.files:
                match file.file_type:
                    case "photo":
                        photos.append(file.file_id)

                    case "document":
                        docs.append(file.file_id)

                    case "video":
                        videos.append(file.file_id)

            return photos, videos, docs

        else:
            return None
