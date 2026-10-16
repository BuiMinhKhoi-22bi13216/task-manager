from .decorator import log_execution_time

class Project:
    def __init__(self, name):
        self.name = name 
        self.tasks = []

    @log_execution_time
    def add_task(self, task):
        self.tasks.append(task)

      
           
