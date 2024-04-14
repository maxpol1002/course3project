from datetime import datetime


class Task:
    def __init__(self, task_id: int, task_name: str, task_description: str, importance_level: int, task_setting_time: datetime,
                 task_deadline: datetime, assigned_users: list):
        self.task_id = task_id
        self.task_name = task_name
        self.task_description = task_description
        self.importance_level = importance_level
        self.task_setting_time = task_setting_time
        self.task_deadline = task_deadline
        self.assigned_users = assigned_users
