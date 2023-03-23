"""
Comenzamos con una solución sencilla que cumple los problemas de seguridad. Más adelante intentaré 
buscar una que resuelva problemas de inanición o deadlock.
"""


import time
import random
from multiprocessing import Lock, Condition, Process
from multiprocessing import Value

SOUTH = 1
NORTH = 0

NCARS = 100
NPED = 10
TIME_CARS = 0.5  # un nuevo coche aparece cada 0.5s
TIME_PED = 5 # un nuevo peaton aparece cada 5s.
TIME_IN_BRIDGE_CARS = (1, 0.5) 
TIME_IN_BRIDGE_PEDESTRIAN = (30, 10) 

class Monitor():
    def __init__(self):
        self.mutex = Lock()
        #número de peatones y coches (en cada dirección) que hay en el puente cada vez:
        self.num_ped = Value('i', 0)
        self.num_car_north = Value('i', 0)
        self.num_car_south = Value('i', 0)
        #lo que nos garantizará que el puente va a ser seguro:
        self.nopeatones = Condition(self.mutex)
        self.nocoches = Condition(self.mutex)
        self.nocoches_norte = Condition(self.mutex)
        self.nocoches_sur = Condition(self.mutex)
        #para poder llevar un conteo de cuántos coches y cuantos peatones ya han pasado el puente:
        self.coches_en_total = Value('i', 0)
        self.peat_en_total = Value('i', 0)
        
    
    def no_pedestrians(self):
        return self.num_ped.value == 0
    
    def no_car_south(self):
        return self.num_car_south.value == 0
    
    def no_car_north(self):
        return self.num_car_north.value == 0
    
    def wants_enter_car(self, direction: int) -> None:
        self.mutex.acquire()
        self.nopeatones.wait_for(self.no_pedestrians)
        #vemos la dirección en la que va y comprobamos que (aparte de que no hayan peatones, que ya ha 
        #sido comprobado), que no hayan coches en dirección contraria en el puente.
        if direction == NORTH:
            self.nocoches_sur.wait_for(self.no_car_south)
            self.num_car_north.value += 1
        else:
            self.nocoches_norte.wait_for(self.no_car_north)
            self.num_car_south.value += 1
        self.coches_en_total.value += 1
        self.mutex.release()

    def leaves_car(self, direction: int) -> None:
        self.mutex.acquire() 
        if direction == NORTH:
            self.num_car_north.value -= 1
            self.nocoches_norte.notify_all() 
        else:
            self.num_car_south.value -= 1
            self.nocoches_sur.notify_all()
        self.nocoches.notify_all()
        self.mutex.release()

    def no_cars(self):
        return self.num_car_north.value == 0 and self.num_car_south.value == 0
    
    def wants_enter_pedestrian(self) -> None:
        self.mutex.acquire()
        self.nocoches.wait_for(self.no_cars) #una vez nos aseguramos que no hay coches en ninguna de las direcciones, dejamos pasar a los peatones.
        self.num_ped.value += 1
        self.peat_en_total.value += 1
        self.mutex.release()

    def leaves_pedestrian(self) -> None:
        self.mutex.acquire()
        self.num_ped.value -= 1
        self.nopeatones.notify_all()
        self.mutex.release()

    def __repr__(self) -> str:
        return f'Peatones: {self.peat_en_total.value}, Coches: {self.coches_en_total.value}'

def delay_car_north() -> None:
    time.sleep(max(random.normalvariate(1, 0.5), 0))

def delay_car_south() -> None:
    time.sleep(max(random.normalvariate(1, 0.5), 0))

def delay_pedestrian() -> None:
    time.sleep(max(random.normalvariate(30, 10), 0)) 
    
    
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

#no veo el fallo para ver por que no termina el programa con los delays activados.
#creo que tiene que ver con que el num del monitor a veces se queda "estancado" porque ocurren varias cosas a la vez (ej. entra un peaton justo en el momento en que otro sale y asi). Pero eso esta permitido no?