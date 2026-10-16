from dataclasses import dataclass
from enum import Enum
from typing import Optional
from datetime import date

@dataclass
class User:
    name: str

class TaskStatus(Enum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"

class TaskPriority(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

@dataclass 
class Task:
    title: str
    assignee: User
    status: TaskStatus = TaskStatus
    priority: TaskPriority = TaskPriority
    task_type: str = "general"
    description: str = " "
    deadline: Optional[date] = None


    def complete(self):
        self.change_status(TaskStatus.DONE)

    def change_status(self, new_status: TaskStatus):
        if self.status == TaskStatus.DONE and new_status != TaskStatus.DONE:
            print("Invalid transition")
            return    
        elif self.status == TaskStatus.IN_PROGRESS and new_status == TaskStatus.TODO:
            print("Invalid transition")
            return
            
        self.status = new_status 


        
