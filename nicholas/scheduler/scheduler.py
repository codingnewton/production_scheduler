from typing import List, Tuple, Union
from ortools.sat.python import cp_model
from .scheduler_classes import Task, Member, ROLE_MEMBERS, time
from collections import defaultdict
import pandas as pd
import numpy as np

# Dependency types
AND_DEP = "and"  # All predecessors must complete before task can start
OR_DEP = "or"    # At least one predecessor must complete before task can start

class EnhancedSolutionCollector(cp_model.CpSolverSolutionCallback):
    def __init__(self, tasks, members, time_unit=15, max_solutions=1000, timeout_seconds=300):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self.tasks = tasks
        self.time_unit = time_unit
        self.max_solutions = max_solutions
        self.timeout_seconds = timeout_seconds
        self.solutions = []
        self.solution_count = 0
        self.members = members
        
    def OnSolutionCallback(self):
        # Convert to human-readable format
        solution = {} 
        for task_id, (_, start_var, end_var, _) in self.tasks.items():
            start = self.Value(start_var) * self.time_unit
            solution[task_id] = start
            
        sol_member_schedule = defaultdict(list)
        for member in self.members:
            for task_id, interval, presence in member.assigned_tasks:
                if self.Value(presence):  # Only include if actually assigned
                    start = self.Value(interval.StartExpr()) * self.time_unit
                    end = self.Value(interval.EndExpr()) * self.time_unit
                    sol_member_schedule[member.id].append({
                        'task': task_id,
                        'start': self._minutes_to_time(start),
                        'end': self._minutes_to_time(end)
                    })
        self.solutions.append((solution, sol_member_schedule))
        self.solution_count += 1
        
        # Stop if reached max solutions
        if self.solution_count >= self.max_solutions:
            print('Stopping search')
            self.StopSearch()
    
    def _minutes_to_time(self, minutes):
        """Convert minutes since midnight to HH:MM format"""
        return f"{minutes//60:02d}:{minutes%60:02d}"
    
    def get_solutions(self):
        return self.solutions
    


class Optimizer:
    def __init__(self, tasks: List[Task], members: List[Member], ot_hours: int = 8):
        """
        Initializes the Optimizer class.

        Args:
            tasks (List[Task]): A list of tasks to be scheduled.
            members (List[Member]): A list of members available to work on the tasks.
            ot_hours (int, optional): The number of regular working hours per member before changing to a predefined OT rate. Defaults to 8.
        """
        self.tasks = tasks
        self.members = members
        self.ot_hours = ot_hours
        self.optimized_cost = np.inf
        self.best_solution = None

    def get_by_id(self, type: Union[List[Task], List[Member]], id: int):
        """Get an object by its ID."""
        return next((obj for obj in type if obj.id == id), None)  
    
    def schedule_tasks(self, get_all_solutions=False, timeout = 30, num_workers = 8, break_duration = 30, max_time_before_break = 240, allow_breaks=True):
        """Schedule tasks using CP-SAT solver."""
        model = cp_model.CpModel()
        
        task_dict = {}
        member_intervals = defaultdict(list)

        # Convert task dependencies to required format
        dependencies = []

        for task in self.tasks:
            # Process dependencies
            if task.dependencies:
                for dep in task.dependencies:
                    if isinstance(dep, tuple):
                        dependencies.append({
                            "successor": task.id,
                            "predecessors": dep,
                            "type": OR_DEP
                        })
                    else:
                        dependencies.append({
                            "successor": task.id,
                            "predecessors": [dep],
                            "type": AND_DEP
                        })

            # Create task interval variables
            start_var = model.NewIntVar(0, int(1440/15), f'start_{task.id}')
            end_var = model.NewIntVar(0, int(1440/15), f'end_{task.id}')
            
            # Time window constraints
            if not task.time_of_day:
                model.Add(end_var == start_var + int(task.estimated_duration/15))
            else:
                task_windows = [(int(self._time_to_minutes(s)/15), int(self._time_to_minutes(e)/15)) for s,e in task.time_of_day]
                window_constraints = []
                for window_start, window_end in task_windows:
                    in_window = model.NewBoolVar(f'task{task.id}_in_window_{window_start}')
                    model.Add(start_var >= window_start).OnlyEnforceIf(in_window)
                    model.Add(end_var <= window_end).OnlyEnforceIf(in_window)
                    window_constraints.append(in_window)
                model.Add(sum(window_constraints) >= 1)
            
            interval_var = model.NewIntervalVar(start_var, int(task.estimated_duration/15), end_var, f'task{task.id}_interval')
            task_dict[task.id] = (task, start_var, end_var, interval_var)

        # Handle member assignments
        for task in self.tasks:
            task_data = task_dict[task.id]
            start_var, end_var = task_data[1], task_data[2]
            
            # Role-based assignments
            for role_id, req_count in task.roles:
                presence_vars = []
                for member_id in ROLE_MEMBERS[role_id]:
                    presence = model.NewBoolVar(f"role_{member_id}_task{task.id}")
                    presence_vars.append(presence)
                    
                    interval = model.NewOptionalIntervalVar(
                        start=start_var,
                        size=int(task.estimated_duration/15),
                        end=end_var,
                        is_present=presence,
                        name=f"role_{member_id}_task{task.id}_interval"
                    )
                    member_intervals[member_id].append((task.id, interval, presence))
                    
                    # Handle blocked timeslots
                    member = self.get_by_id(self.members, member_id)
                    self._add_blocked_time_constraints(model, member, start_var, end_var, presence)
                    
                model.Add(sum(presence_vars) == req_count)
            
            # Direct member assignments
            for member_id in task.members:
                assign_var = model.NewBoolVar(f'task{task.id}_mem{member_id}')
                model.Add(assign_var == 1)  # Must be assigned
                
                interval = model.NewOptionalIntervalVar(
                    start=start_var,
                    size=int(task.estimated_duration/15),
                    end=end_var,
                    is_present=assign_var,
                    name=f"direct_{member_id}_task{task.id}_interval"
                )
                member_intervals[member_id].append((task.id, interval, assign_var))
                
                # Handle blocked timeslots
                member = self.get_by_id(self.members, member_id)
                self._add_blocked_time_constraints(model, member, start_var, end_var, assign_var)

        # Handle dependencies
        for dep in dependencies:
            successor_id = dep["successor"]
            predecessor_ids = dep["predecessors"]
            dep_type = dep["type"]
            successor_start = task_dict[successor_id][1]
                        
            if dep_type == AND_DEP:
                for pred_id in predecessor_ids:
                    model.Add(successor_start >= task_dict[pred_id][2])
            elif dep_type == OR_DEP:
                or_constraints = []
                for pred_id in predecessor_ids:
                    or_condition = model.NewBoolVar(f'pred_{pred_id}before_succ{successor_id}')
                    model.Add(successor_start >= task_dict[pred_id][2]).OnlyEnforceIf(or_condition)
                    or_constraints.append(or_condition)
                model.AddAtLeastOne(or_constraints)

        # Add break constraints for each member
        for member_id, intervals in member_intervals.items():
            if not intervals:
                continue
            
            member = self.get_by_id(self.members, member_id)
            member.assigned_tasks = intervals            
            member_intervals_list = [interval[1] for interval in intervals]
            
            # Create a break interval for the member
            # Calculate total duration of assigned tasks
            total_duration = model.NewIntVar(0, int(1440/15), f'total_duration_{member_id}')
            model.Add(total_duration == sum(interval[1].SizeExpr() for interval in intervals))

            # Calculate number of breaks needed
            max_time_slots = int(max_time_before_break/15)  # Convert to 15-min slots
            break_duration_slots = int(break_duration/15)

            # Create break intervals based on total duration
            break_intervals = []
            
            if allow_breaks:
                for i in range(int(1440/max_time_before_break)):  # Maximum possible breaks in a day
                    # Create a boolean to determine if this break is needed
                    need_break = model.NewBoolVar(f'need_break_{member_id}_{i}')
                    
                    # This break is needed if total duration > max_time_before_break * (i+1)
                    model.Add(total_duration >= max_time_slots * (i+1)).OnlyEnforceIf(need_break)
                    model.Add(total_duration < max_time_slots * (i+1)).OnlyEnforceIf(need_break.Not())

                    break_start = model.NewIntVar(0, int(1440/15), f'break_start_{member_id}_{i}')
                    break_end = model.NewIntVar(0, int(1440/15), f'break_end_{member_id}_{i}')
                    
                    # Break must start after minimum time but before maximum allowed time
                    min_start = max_time_slots * (i+1) - int(60/15)  # 60 minutes before max time
                    max_start = max_time_slots * (i+1) + int(60/15)  # 60 minutes after max time
                    
                    model.Add(break_start >= min_start).OnlyEnforceIf(need_break)
                    model.Add(break_start <= max_start).OnlyEnforceIf(need_break)
                    
                    break_interval = model.NewOptionalIntervalVar(
                        break_start,
                        break_duration_slots,
                        break_end,
                        need_break,
                        f'break_interval_{member_id}_{i}'
                    )
                    break_intervals.append(break_interval)

            # Add breaks to member's intervals to prevent overlap
            all_intervals = member_intervals_list + break_intervals
            model.AddNoOverlap(all_intervals)
                    
        # Optimized cost calculation
        total_cost = self._calculate_costs(model, member_intervals)
        model.Minimize(total_cost)
        
        # Solve and process results
        return self._solve_and_process_results(model, task_dict, return_solutions_only=get_all_solutions, timeout=timeout, num_workers=num_workers)

    def _add_blocked_time_constraints(self, model, member, start_var, end_var, presence_var):
        """Helper method to add blocked time constraints for a member"""
        member_blocked_timeslot = [
            (int(self._time_to_minutes(s)/15), int(self._time_to_minutes(e)/15)) 
            for s, e in member.blocked_timeslots
        ]
        
        for block_start, block_end in member_blocked_timeslot:
            before = model.NewBoolVar(f"mem{member.id}_before_{block_start}")
            after = model.NewBoolVar(f"mem{member.id}_after_{block_end}")
                                
            model.Add(end_var <= block_start).OnlyEnforceIf(before)
            model.Add(start_var >= block_end).OnlyEnforceIf(after)
            
            # At least one must be true if member is assigned
            model.AddBoolOr([before, after]).OnlyEnforceIf(presence_var)

    def _calculate_costs(self, model, member_intervals):
        """Cost calculation"""
        total_cost = 0
        
        for member_id, intervals in member_intervals.items():
            if not intervals:
                continue

            member = self.get_by_id(self.members, member_id)
            
            # Calculate time span using adjusted dummy values
            starts = [interval[1].StartExpr() for interval in member.assigned_tasks]
            ends = [interval[1].EndExpr() for interval in member.assigned_tasks]
            
            earliest_start = model.NewIntVar(0, int(1440/15), f'earliest_start_{member_id}')
            latest_end = model.NewIntVar(0, int(1440/15), f'latest_end_{member_id}')
            
            # For unassigned tasks, starts will have 1440 and ends 0
            model.AddMinEquality(earliest_start, starts)
            model.AddMaxEquality(latest_end, ends)
            
            # Create conditional time span
            time_span = model.NewIntVar(0, int(1440/15), f'time_span_{member_id}')
            model.Add(time_span == latest_end - earliest_start)
            
            # Improved overtime calculation
            regular_hours = int(self.ot_hours * 60/15)
            regular_time = model.NewIntVar(0, regular_hours, f'reg_time_{member_id}')
            overtime = model.NewIntVar(0, int(1440/15) - regular_hours, f'ot_{member_id}')
            
            # Use linear constraints instead of conditional
            model.AddMinEquality(regular_time, [time_span, regular_hours])
            model.Add(overtime == time_span - regular_time)
            
            # Calculate cost
            member_cost = model.NewIntVar(0, 999999999, f'cost_{member_id}')
            rate = int(member.rate * 15/60)
            ot_rate = int(member.ot * 15/60)
            model.Add(member_cost == regular_time* rate + overtime* ot_rate)
            total_cost += member_cost
        return total_cost

    def _solve_and_process_results(self, model, task_dict, return_solutions_only=False, timeout=30, num_workers=8):
        """Process solving results and return schedule"""
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = timeout
        solver.parameters.num_search_workers = num_workers
        
        # This will return all solutions found before timeout
        if return_solutions_only:
            collector = EnhancedSolutionCollector(
                tasks=task_dict,
                members=self.members,
                time_unit=15,
                max_solutions=100,  # Return first 100 solutions
                timeout_seconds=timeout  # Stop after 1 minute
            )
            
            status = solver.Solve(model, collector)
            
            if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
                print('Status')
                print(f'Found {collector.solution_count} solutions in {timeout:.2f} seconds')
                solutions = collector.get_solutions()
                self.best_solution = solutions
                return solutions
            
        status = solver.Solve(model)
        print(status)

        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            # Build schedule
            solution = {}
            for task_id, (_, start_var, _, _) in task_dict.items():
                start = solver.Value(start_var) * 15
                solution[task_id] = start
            
            # Set member schedules
            sol_member_schedule = defaultdict(list)
            for member in self.members:
                for task_id, interval, presence in member.assigned_tasks:
                    if solver.Value(presence):  # Only include if actually assigned
                        start = solver.Value(interval.StartExpr()) * 15
                        end = solver.Value(interval.EndExpr()) * 15
                        sol_member_schedule[member.id].append({
                            'task': task_id,
                            'start': self._minutes_to_time(start),
                            'end': self._minutes_to_time(end)
                        })
                        
            self.optimized_cost = solver.ObjectiveValue()
            self.best_solution = [(solution, sol_member_schedule)]
            
        return self.best_solution
        
    def _minutes_to_time(self, minutes):
        """Convert minutes since midnight to HH:MM format"""
        return f"{minutes//60:02d}:{minutes%60:02d}"
    
    def _time_to_minutes(self, t: time) -> int:
      """Convert time object to minutes since midnight."""
      return t.hour * 60 + t.minute    
