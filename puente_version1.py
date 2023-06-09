

"""
En esta versión tratamos de resolver los problemas de inanición resgulando el paso de peatones y coches
(indistintamente de su dirección), de modo que si muchos coches han ido pasando seguidos se les dará paso a 
los peatones y viceversa.
"""



import time
import random
from multiprocessing import Lock, Condition, Process
from multiprocessing import Value

SOUTH = 1
NORTH = 0

NCARS = 100
NPED = 10
TIME_CARS = 0.5  
TIME_PED = 5 
TIME_IN_BRIDGE_CARS = (1, 0.5) 
TIME_IN_BRIDGE_PEDESTRIAN = (30, 10) 

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
        self.nocoches_sur = Condition(self.mutex) #
        self.max_coches = Value('i', 0) #contabiliza los coches seguidos que entran al puente.
        self.max_peatones = Value('i', 0)#lo mismo con los peatones
        self.muchos_coches = Condition(self.mutex)
        self.muchos_peatones = Condition(self.mutex)
        self.coches_waiting = Value('i', 0)
        self.peat_waiting = Value('i', 0)
        self.peat_en_total = Value('i', 0)
        self.coches_en_total = Value('i', 0)

    def no_pedestrians(self):
        return self.num_ped.value == 0
    
    def no_car_south(self):
        return self.num_car_south.value == 0
    
    def no_car_north(self):
        return self.num_car_north.value == 0
    
    def demasiados_coches(self):
        return self.max_coches.value < 15 #por ejemplo metemos ese número. Si han pasado más de 15 coches seguidos, damos paso a los peatones.
    
    def wants_enter_car(self, direction: int) -> None:
        self.mutex.acquire()
        self.coches_waiting.value += 1 #para comprobar los que están esperando, por si no hay ninguno que no se tenga en cuenta para darles paso.
        if self.peat_waiting.value != 0: #si no hay peatones esperando, no nos interesa esta condición.
            self.muchos_coches.wait_for(self.demasiados_coches) #para dar paso a los peatones que haya esperando
        self.nopeatones.wait_for(self.no_pedestrians)
        if direction == NORTH:
            self.nocoches_sur.wait_for(self.no_car_south)
            self.num_car_north.value += 1
        else:
            self.nocoches_norte.wait_for(self.no_car_north)
            self.num_car_south.value += 1
        self.max_coches.value += 1
        self.max_peatones.value = 0 #como pasa un coche al puente, podemos poner el número de peatones seguidos a 0.
        self.muchos_peatones.notify_all() #como ya se ha dejado pasar a un coche, avisamos a los peatones de que ya pueden volver a empezar a pasar. 
        self.coches_waiting.value -= 1 #el coche que ha entrado ya deja de contar como coche esperando.
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
    
    def demasiados_peatones(self):
        return self.max_peatones.value < 5 #ponemos menos que los coches porque tardan más en pasar, pero es un valor variable,
    
    def wants_enter_pedestrian(self) -> None:
        self.mutex.acquire()
        self.peat_waiting.value += 1
        if self.coches_waiting.value != 0: #si no hay coches esperando, no nos interesa esta condición.
            self.muchos_peatones.wait_for(self.demasiados_peatones)
        self.nocoches.wait_for(self.no_cars)
        self.num_ped.value += 1
        self.max_peatones.value += 1
        self.max_coches.value = 0
        self.muchos_coches.notify_all() #avisamos a los coches de que ya podrían empear a pasar
        self.peat_waiting.value -= 1
        self.peat_en_total.value += 1
        self.mutex.release()

    def leaves_pedestrian(self) -> None:
        self.mutex.acquire()
        self.num_ped.value -= 1
        self.nopeatones.notify_all()
        self.mutex.release()

    def __repr__(self) -> str:
        return f'Peatones: {self.peat_en_total.value}, Coches: {self.coches_en_total.value}, Peatones esperando: {self.peat_waiting.value}, Coches esperando: {self.coches_waiting.value}'

def delay_car_north() -> None:
    time.sleep(max(random.normalvariate(1, 0.5),0))

def delay_car_south() -> None:
    time.sleep(max(random.normalvariate(1, 0.5),0))

def delay_pedestrian() -> None:
    time.sleep(max(random.normalvariate(30, 10),0))  #por si sale algún número negativo.
    
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

