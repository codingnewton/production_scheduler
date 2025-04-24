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