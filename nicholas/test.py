from scheduler import Member, Task, Optimizer, export_schedules
from datetime import time

members = []
Jacob = Member(0, "Jacob", [(time(0, 0), time(8, 0)), (time(18, 0), time(23, 59))], 100, 150, 0, 0.5)
Vicky = Member(1, "Vicky", [(time(0, 0), time(8, 0)), (time(18, 0), time(23, 59))], 300, 350, 0, 0.5)
Monita = Member(2, "Monita", [(time(0, 0), time(8, 0)), (time(18, 0), time(23, 59))], 200, 250, 0, 0.5)
Ray = Member(3, "Ray", [(time(0, 0), time(8, 0)), (time(18, 0), time(23, 59))], 600, 750, 0, 0.5)
John = Member(4, "John", [(time(0, 0), time(12, 0)), (time(21, 0), time(23, 59))], 200, 250, 1, 0.5)
Sara = Member(5, "Sara", [(time(0, 0), time(11, 0)), (time(21, 0), time(23, 59))], 200, 250, 1, 0.5)
Raj = Member(6, "Raj", [(time(0, 0), time(8, 0)), (time(21, 0), time(23, 59))], 200, 250, 1, 0.5)
Kumar = Member(7, "Kumar", [(time(0, 0), time(8, 0)), (time(17, 0), time(23, 59))], 200, 250, 1, 0.5)
Rahul = Member(8, "Rahul", [(time(0, 0), time(8, 0)), (time(18, 0), time(23, 59))], 300, 350, 1, 0.5)
Rajesh = Member(9, "Rajesh", [(time(0, 0), time(23, 59))], 300, 350, 1, 0.5)
Ramesh = Member(10, "Ramesh", [(time(0, 0), time(8, 0)), (time(21, 0), time(23, 59))], 450, 450, 1, 0.5)
Rajat = Member(11, "Rajat", [(time(0, 0), time(8, 0)), (time(21, 0), time(23, 59))], 450, 450, 1, 0.5)
Bonnie = Member(12, "Bonnie", [(time(0, 0), time(8, 0)), (time(21, 0), time(23, 59))], 450, 550, 2, 0.5)
Sheila = Member(13, "Sheila", [(time(0, 0), time(8, 0)), (time(21, 0), time(23, 59))], 450, 550, 2, 0.5)
Sandy = Member(14, "Sandy", [(time(0, 0), time(14, 0)), (time(21, 0), time(23, 59))], 250, 300, 2, 0.5)
Camera1 = Member(15, "Camera1", [(time(0, 0), time(9, 0)), (time(20, 0), time(23, 59))], 50, 50, 4, 0.5)
Camera2 = Member(16, "Camera2", [(time(8, 0), time(14, 0)), (time(23, 0), time(23, 59))], 50, 50, 4, 0.5)
Camera3 = Member(17, "Camera3", [(time(0, 0), time(8, 0)), (time(21, 0), time(23, 59))], 50, 50, 4, 0.5)
Camera4 = Member(18, "Camera4", [(time(0, 0), time(8, 0)), (time(21, 0), time(23, 59))], 50, 50, 4, 0.5)
Camera5 = Member(19, "Camera5", [(time(0, 0), time(8, 0)), (time(21, 0), time(23, 59))], 50, 50, 4, 0.5)

members = [Jacob, Vicky, Monita, Ray, John, Sara, Raj, Kumar, Rahul, Rajesh, Ramesh, Rajat, Bonnie, Sheila, 
           Sandy, Camera1, Camera2, Camera3, Camera4, Camera5]
JacobMakeup = Task(0, ["Parking Lot Near Loading Bay"], 30, members=[0], roles=[(2, 1)])
SetupLightingParkingLot = Task(1, ["Parking Lot Near Loading Bay"], 75, roles=[(1, 5), (4, 2)], members=[15])
VickyMakeup = Task(2, ["Parking Lot Near Loading Bay"], 75, members=[1, 13])
JacobShot = Task(3, ["Parking Lot Near Loading Bay"], 60, members=[0, 15], roles=[(1, 5),(4, 2)], dependencies=[(0, 5), 1])
VickyPhotoshoot = Task(4, ["The Galleria", "Studio"], 60, members=[1], roles=[(1, 2),(4, 2)], dependencies=[20, (2, 8)])
JacobMakeupTouchUp = Task(5, ["Parking Lot Near Loading Bay"], 15, members=[0], roles=[(2, 1)], dependencies=[0, (3, 7)])
SetupLightingExt = Task(6, ["Parking Lot Near Loading Bay"], 60, roles=[(1, 5), (4, 2)], members=[15])
JacobPhotoshoot = Task(7, ["The Galleria", "Studio"], 60, members=[0], roles=[(1, 2),(4, 2)], dependencies=[20, (0, 5)])
VickyMakeupTouchUp = Task(8, ["Parking Lot Near Loading Bay", "The Galleria", "Studio"], 15, members=[1,13], roles=[(2, 1)], dependencies=[2, (4, 9)])
VickyShot = Task(9, ["Parking Lot Near Loading Bay"], 30, members=[1, 15], roles=[(1, 5),(4, 2)], dependencies=[(2, 8), 6])
# Lunch = Task(10, ["Cathay City Loading Bay"], 60, roles=[(1, 5), (4, 2)], members=[15])
RayMakeup = Task(10, ["Entrance"], 45, members=[3], roles=[(2, 1)])
SetupLightingEntrance = Task(11, ["Entrance"], 105, roles=[(1, 5), (4, 2)], members=[15])
MonitaMakeup = Task(12, ["The Galleria", "Studio"], 75, members=[2, 13])
RayShot = Task(13, ["Entrance"], 60, members=[3, 15], roles=[(1, 5), (4, 2)], dependencies=[11, (10, 15)])
MonitaPhotoshoot = Task(14, ["The Galleria", "Studio"], 60, members=[2], roles=[(1, 2),(4, 2)], dependencies=[20, (12, 18)])
RayMakeupTouchUp = Task(15, ["Entrance"], 15, members=[3], roles=[(2, 1)], dependencies=[10, (13, 17)])
SetupLightingStreet = Task(16, ["The Street"], 45, roles=[(1, 5), (4, 2)], members=[15])
RayPhotoshoot = Task(17, ["The Galleria", "Studio"], 60, members=[3], roles=[(1, 2),(4, 2)], dependencies=[20])
MonitaMakeupTouchUp = Task(18, ["Parking Lot Near Loading Bay", "The Galleria", "Studio"], 30, members=[1,13], roles=[(2, 1)], dependencies=[2, (4, 9)])
MonitaShot = Task(19, ["Parking Lot Near Loading Bay"], 60, members=[2, 15], roles=[(1, 5),(4, 2)], dependencies=[8, (4, 9)])
SetupPhotoArea = Task(20, ["The Galleria", "Studio"], 30, roles=[(1, 2), (4, 2)])

tasks = [JacobMakeup, SetupLightingParkingLot, VickyMakeup, JacobShot, VickyPhotoshoot, JacobMakeupTouchUp, SetupLightingExt, JacobPhotoshoot, VickyMakeupTouchUp, VickyShot, 
         RayMakeup, SetupLightingEntrance, MonitaMakeup, RayShot, MonitaPhotoshoot, RayMakeupTouchUp, SetupLightingStreet, RayPhotoshoot, MonitaMakeupTouchUp, MonitaShot, SetupPhotoArea]

model = Optimizer(tasks, members)
res = model.schedule_tasks(timeout=60)
print('The optimized cost is: ', model.optimized_cost)
export_schedules(res, model, location=r'C:\Users\nicho\OneDrive - HKUST Connect\Study\FYP\output')