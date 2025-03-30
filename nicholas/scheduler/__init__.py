from .scheduler import Optimizer, List
from .scheduler_classes import Member, Task, ROLE_NAME, LOCATIONS, TRANSPORTATION_TIME
from .export_schedules import export_schedules

class Optimizer(Optimizer):
    def __init__(self, tasks: List[Task], members: List[Member], ot_hours: int = 8):
        super().__init__(tasks, members, ot_hours)

    def export_schedule(self, export_location=''):
        export_schedules(self.res, self, export_location=export_location)