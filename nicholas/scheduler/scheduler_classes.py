from typing import List, Tuple, Optional, Union
from datetime import time
from pydantic import BaseModel, Field, validator, root_validator

# Input parameters
ROLE_NAME = {
    0: "Actor",
    1: "Shooting Crew",
    2: "Makeup Crew",
    3: "Lighting Crew",
    4: "Equipment"
}

ROLE_MEMBERS = {i:[] for i in ROLE_NAME.keys()}

# def time_to_minutes(t: time) -> int:
#     """Convert time object to minutes since midnight."""
#     return t.hour * 60 + t.minute
# def minutes_to_time(minutes: int) -> time:
#     """Convert minutes since midnight to time object."""
#     # Handle overflow
#     minutes = minutes % (24 * 60)  # Keep within 24 hours
#     hours = minutes // 60
#     mins = minutes % 60
#     return time(hour=int(hours), minute=int(mins))
# def get_time_difference(start: time, end: time) -> int:
#     """Calculate minutes between two time objects.
    
#     Args:
#         start: Start time
#         end: End time
        
#     Returns:
#         int: Minutes between times, handling overnight periods
#     """
#     start_minutes = start.hour * 60 + start.minute
#     end_minutes = end.hour * 60 + end.minute
    
#     # Handle overnight cases (when end time is earlier than start time)
#     if end_minutes < start_minutes:
#         end_minutes += 24 * 60  # Add 24 hours in minutes
        
#     return end_minutes - start_minutes

class Task(BaseModel):
    id: int  # Add this line
    estimated_duration: int
    location: List[str] = []
    description: str = ""
    dependencies: List[Union[int, Tuple[int, int]]] = []
    time_of_day: List[Tuple[time, time]] = [(time(0, 0), time(23, 59))]
    members: List[int] = [],
    roles: List[Tuple[int, int]] = []
     
    @root_validator(pre=True)
    def check_members_or_roles(cls, values):
        if not values.get('members') and not values.get('roles'):
            raise ValueError("Task must have either members or roles specified.")
        return values

    def __str__(self):
        return f"Task({str(self.id)},{str(self.estimated_duration)},{str(self.location)},\
{str(self.description)},{str(self.dependencies)},{str(self.time_of_day)},{str(self.members)},{str(self.roles)})"

class Member(BaseModel):
    id: int
    name: str
    rate: int
    ot: int
    role: int  # Role ID
    blocked_timeslots: List[Tuple[time, time]] = Field(default_factory=list)
    transportation_speed: float = 0.5  # scale from 0 to 1, lower is faster
    working_hours: List[time] = Field(default_factory=list)
    assigned_tasks: List = Field(default_factory=list)
    schedule: List = Field(default_factory=list)
    
    def model_post_init(self, __context):
        """This runs after the model is initialized"""
        self._set_role()
    
    def __str__(self):
        return f"Member({str(self.id)},{str(self.name)},{str(self.rate)},{str(self.ot)},{str(self.role)},blocked_timeslots={str(self.blocked_timeslots)},transportation_speed={str(self.transportation_speed)})"

    def _set_role(self):
        global ROLE_MEMBERS
        if self.role not in ROLE_MEMBERS:
            ROLE_MEMBERS[self.role] = []
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