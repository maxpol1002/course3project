from classes.File import File

import db


class Report:
    def __init__(self, report_id: int, user_id: int, task_id: int, send_time: str, report_text: str, report_status: str,
                 task_name: str, files: list[File] or None):
        self.report_id = report_id
        self.user_id = user_id
        self.task_id = task_id
        self.send_time = send_time
        self.report_text = report_text
        self.report_status = report_status
        self.task_name = task_name
        self.files = files

    def create_report_text(self) -> str:
        data = (
            "======================================\n"
            f"Report ID: {self.report_id}\n"
            f"Task name: {self.task_name}\n"
            f"Executor: {db.db_get_user_data(user_id=self.user_id)}\n" 
            f"Time sent: {self.send_time}\n"
            f"Report text: {self.report_text}\n"
            f"Report status: {self.report_status}\n"
            "======================================"

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
