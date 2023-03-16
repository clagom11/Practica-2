"""
Solution to the one-way tunnel
Comenzamos con una solución sencilla que cumple los problemas de seguridad. Más adelante intentaré 
buscar una que resuelva problemas de inanición o deadlock.
"""


#PREGUNTAR BIEN LO DEL TIEMPO!!!

import time
import random
from multiprocessing import Lock, Condition, Process
from multiprocessing import Value

SOUTH = 1
NORTH = 0

NCARS = 100
NPED = 10
TIME_CARS = 0.5  # a new car enters each 0.5s
TIME_PED = 5 # a new pedestrian enters each 5s
TIME_IN_BRIDGE_CARS = (1, 0.5) # normal 1s, 0.5s
TIME_IN_BRIDGE_PEDESTRIAN = (30, 10) # normal 1s, 0.5s

class Monitor():
    def __init__(self):
        self.mutex = Lock()
        self.patata = Value('i', 0)
        self.num_ped = Value('i', 0)
        self.num_car_north = Value('i', 0)
        self.num_car_south = Value('i', 0)
        self.nopeatones = Condition(self.mutex)
        self.nocoches = Condition(self.mutex)
        self.nocoches_norte = Condition(self.mutex)
        self.nocoches_sur = Condition(self.mutex) #no sé si será así todos con el mutex
    
    def no_pedestrians(self):
        return self.num_ped.value == 0
    
    def no_car_south(self):
        return self.num_car_south.value == 0
    
    def no_car_north(self):
        return self.num_car_north.value == 0
    
    def wants_enter_car(self, direction: int) -> None:
        self.mutex.acquire()
        self.patata.value += 1
        #### código
        self.nopeatones.wait_for(self.no_pedestrians)
        if direction == NORTH:
            self.nocoches_sur.wait_for(self.no_car_south)
            self.num_car_north.value += 1
        else:
            self.nocoches_norte.wait_for(self.no_car_north)
            self.num_car_south.value += 1
        self.mutex.release()

    def leaves_car(self, direction: int) -> None:
        self.mutex.acquire() 
        self.patata.value += 1
        #### código
        if direction == NORTH:
            self.num_car_north.value -= 1
            self.nocoches_norte.notify()
        else:
            self.num_car_south.value -= 1
            self.nocoches_sur.notify()
        self.nocoches.notify()
        self.mutex.release()

    def no_cars(self):
        return self.num_car_north.value == 0 and self.num_car_south.value == 0
    def wants_enter_pedestrian(self) -> None:
        print("numero peatones:", self.num_ped.value)
        self.mutex.acquire()
        self.patata.value += 1
        #### código
        self.nocoches.wait_for(self.no_cars)
        self.num_ped.value += 1
        self.mutex.release()

    def leaves_pedestrian(self) -> None:
        self.mutex.acquire()
        self.patata.value += 1
        #### código
        self.num_ped.value -= 1
        self.nopeatones.notify()
        self.mutex.release()

    def __repr__(self) -> str:
        return f'Monitor: {self.patata.value}'

def delay_car_north() -> None:
    pass

def delay_car_south() -> None:
    pass

def delay_pedestrian() -> None:
    pass

def car(cid: int, direction: int, monitor: Monitor)  -> None:
    print(f"car {cid} heading {direction} wants to enter. {monitor}")
    monitor.wants_enter_car(direction)
    print(f"car {cid} heading {direction} enters the bridge. {monitor}")
    if direction==NORTH :
        delay_car_north()
    else:
        delay_car_south()
    print(f"car {cid} heading {direction} leaving the bridge. {monitor}")
    monitor.leaves_car(direction)
    print(f"car {cid} heading {direction} out of the bridge. {monitor}")

def pedestrian(pid: int, monitor: Monitor) -> None:
    print(f"pedestrian {pid} wants to enter. {monitor}")
    monitor.wants_enter_pedestrian()
    print(f"pedestrian {pid} enters the bridge. {monitor}")
    delay_pedestrian()
    print(f"pedestrian {pid} leaving the bridge. {monitor}")
    monitor.leaves_pedestrian()
    print(f"pedestrian {pid} out of the bridge. {monitor}")



def gen_pedestrian(monitor: Monitor) -> None:
    pid = 0
    plst = []
    for _ in range(NPED):
        pid += 1
        p = Process(target=pedestrian, args=(pid, monitor))
        p.start()
        plst.append(p)
        time.sleep(random.expovariate(1/TIME_PED))

    for p in plst:
        p.join()

def gen_cars(monitor) -> Monitor:
    cid = 0
    plst = []
    for _ in range(NCARS):
        direction = NORTH if random.randint(0,1)==1  else SOUTH
        cid += 1
        p = Process(target=car, args=(cid, direction, monitor))
        p.start()
        plst.append(p)
        time.sleep(random.expovariate(1/TIME_CARS))

    for p in plst:
        p.join()

def main():
    monitor = Monitor()
    gcars = Process(target=gen_cars, args=(monitor,))
    gped = Process(target=gen_pedestrian, args=(monitor,))
    gcars.start()
    gped.start()
    gcars.join()
    gped.join()


if __name__ == '__main__':
    main()

