from typing import List, Tuple
from datetime import time
import numpy as np

# Input parameters
ROLE_NAME = {
    0: "Actor",
    1: "Shooting Crew",
    2: "Makeup Crew",
    3: "Lighting Crew",
    4: "Equipment"
}

# Dependency types
AND_DEP = "and"  # All predecessors must complete before task can start
OR_DEP = "or"    # At least one predecessor must complete before task can start

ROLE_MEMBERS = {i:[] for i in ROLE_NAME.keys()}
LOCATIONS = ["Cathay City Loading Bay", "Exteriors Near Parking Lot", "Parking Lot Near Loading Bay", "Entrance", "The Street", "The Galleria", "Studio", "Recruitment Room"]
TRANSPORTATION_TIME = np.array([[0, 5, 10, 15, 20, 25],[5, 0, 5, 10, 15, 20],[10, 5, 0, 5, 10, 15],[15, 10, 5, 0, 5, 10],[20, 15, 10, 5, 0, 5],[25, 20, 15, 10, 5, 0]])

def time_to_minutes(t: time) -> int:
    """Convert time object to minutes since midnight."""
    return t.hour * 60 + t.minute
def minutes_to_time(minutes: int) -> time:
    """Convert minutes since midnight to time object."""
    # Handle overflow
    minutes = minutes % (24 * 60)  # Keep within 24 hours
    hours = minutes // 60
    mins = minutes % 60
    return time(hour=int(hours), minute=int(mins))
def get_time_difference(start: time, end: time) -> int:
    """Calculate minutes between two time objects.
    
    Args:
        start: Start time
        end: End time
        
    Returns:
        int: Minutes between times, handling overnight periods
    """
    start_minutes = start.hour * 60 + start.minute
    end_minutes = end.hour * 60 + end.minute
    
    # Handle overnight cases (when end time is earlier than start time)
    if end_minutes < start_minutes:
        end_minutes += 24 * 60  # Add 24 hours in minutes
        
    return end_minutes - start_minutes
class Task:
    def __init__(self, id: int, location: List[str], estimated_duration: int,
                #  estimated_cost: int, 
                 description: str = "",
                 dependencies: List[int] = [],
                 time_of_day: List[Tuple[time, time]] = [(time(0, 0), time(23, 59))], 
                 members: List[int] = None, roles: List[Tuple[int, int]] = None):
        
        if not members and not roles:
            raise ValueError("Task must have either members or roles specified.")
        
        self.id = id
        self.location = location
        self.estimated_duration = estimated_duration
        self.description = description
        self.dependencies = dependencies # List[Task ID, (Task ID, Task ID)] 
        self.time_of_day = time_of_day
        self.members = members or []
        self.roles = roles or []    # List[(role, number of members)]
        
        
class Member:
    def __init__(self, id: int, name: str, 
                 rate: int, ot: int, role: int, blocked_timeslots: List[Tuple[time, time]] = [], transportation_speed=0.5):
        self.id = id
        self.name = name
        self.rate = rate
        self.ot = ot
        self.role = role    # Role ID
        self.blocked_timeslots = blocked_timeslots
        self.transportation_speed = transportation_speed    # scale from 0 to 1, lower is faster
        self.working_hours = []
        self.assigned_tasks = []
        self.schedule = []
        self._set_role()

    def _set_role(self):
        global ROLE_MEMBERS
        ROLE_MEMBERS[self.role].append(self.id)

    def get_role(self) -> str:
        global ROLE_NAME
        return ROLE_NAME[self.role]
    
    def is_available_on(self, start_time: time, end_time: time) -> bool:
        """Check if the actor is available on the given date."""
        return not any((start <= start_time < end) or (start <= end_time < end) for start, end in self.blocked_timeslots)
    
    def block_time(self, start_time: time, end_time: time):
        """Block the time slot for the actor."""
        if self.working_hours: 
            self.working_hours = [min(self.working_hours[0], start_time), max(self.working_hours[1], end_time)]
        else: 
            self.working_hours = [start_time, end_time]
        self.blocked_timeslots.append((start_time, end_time))
