from .scheduler import Optimizer, List
from .scheduler_classes import Member, Task, ROLE_NAME
from .export_schedules import export_schedules

class Optimizer(Optimizer):
    def __init__(self, tasks: List[Task], members: List[Member], ot_hours: int = 8):
        super().__init__(tasks, members, ot_hours)

    def export_schedule(self, export_location=''):
        """Export the best solution to a file or location."""
        if not self.best_solution:
            print("No solution found.")
            return
        export_schedules(self.best_solution, self, export_location=export_location)