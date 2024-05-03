from datetime import datetime

import db


class Task:
    def __init__(self, task_id: int, task_name: str, task_description: str, importance_level: int, task_setting_time: datetime,
                 task_deadline: datetime, assigned_users: list, task_status: str):
        self.task_id = task_id
        self.task_name = task_name
        self.task_description = task_description
        self.importance_level = importance_level
        self.task_setting_time = task_setting_time
        self.task_deadline = task_deadline
        self.assigned_users = assigned_users
        self.task_status = task_status

    def print_data(self) -> str:
        assigned_users_str = ', '.join([db.db_get_user_data(user_id) for user_id in self.assigned_users])
        data = (
            f"Task {self.task_id}: {self.task_name}\n"
            f"- Description: {self.task_description}\n"
            f"- Importance level: {self.importance_level}\n"
            f"- Date of issue: {self.task_setting_time}\n"
            f"- Deadline: {self.task_deadline}\n"
            f"- Assigned for: {assigned_users_str}\n"
            f"- Status: {self.task_status}"
        )

        return data

    def print_for_user(self, idx: int) -> str:
        data = (
            f"Task {idx}: {self.task_name}\n"
            f"Description: {self.task_description}\n"
            f"Importance level: {self.importance_level}\n"
            f"Date of issue: {self.task_setting_time}\n"
            f"Deadline: {self.task_deadline}\n"
        )

        return data
