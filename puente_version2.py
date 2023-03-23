"""
Finalmente en esta última versión, nos encontramos con que también se resolverán probalemas de inanición entre 
los coches que van hacia el norte y aquellos que van hacia el sur. Es decir, nos aseguraremos de que, cuando se 
les de paso a los coches, no hay algunos en una dirección que nunca pasen. Partimos de la versión anterior y
añadimos lo necesario para que nuestro programa haga lo que se acaba de explicar.
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
        self.nocoches_sur = Condition(self.mutex) 
        self.max_coches = Value('i', 0) 
        self.max_peatones = Value('i', 0)
        self.muchos_coches = Condition(self.mutex)
        self.muchos_peatones = Condition(self.mutex)
        self.coches_waiting = Value('i', 0)
        self.peat_waiting = Value('i', 0)
        self.peat_en_total = Value('i', 0)
        self.coches_en_total = Value('i', 0)
        #aqui escribimos las variables nuevas, necesarias para resgular el paso de los coches en distinta dirección.
        self.max_coches_norte = Value('i',0)
        self.max_coches_sur = Value('i',0)
        self.muchos_cochesN = Condition(self.mutex)
        self.muchos_cochesS = Condition(self.mutex)
        self.cochesN_waiting = Value('i', 0)
        self.cochesS_waiting = Value('i', 0)

    def no_pedestrians(self):
        return self.num_ped.value == 0
    
    def no_car_south(self):
        return self.num_car_south.value == 0
    
    def no_car_north(self):
        return self.num_car_north.value == 0
    
    def demasiados_coches(self):
        return self.max_coches.value < 15 #por ejemplo metemos ese número.
    
    def demasiados_cochesN(self):
        return self.max_coches_norte.value < 7
    def demasiados_cochesS(self):
        return self.max_coches_sur.value < 7
    
    #se implementará lo mismo que se ha hecho en la versión anterior (e incluido en esta) entre coches 
    #y peatones, para los coches en direcciones contrarias, se escribe exactamente lo mismo.
    def wants_enter_car(self, direction: int) -> None:
        self.mutex.acquire()
        self.coches_waiting.value += 1 
        if self.peat_waiting.value != 0: 
            self.muchos_coches.wait_for(self.demasiados_coches) 
        self.nopeatones.wait_for(self.no_pedestrians)
        if direction == NORTH:
            self.cochesN_waiting.value += 1
            if self.cochesS_waiting.value != 0: #si no hay coches en dirección contraria, no merece la pena darles paso.
                self.muchos_cochesN.wait_for(self.demasiados_cochesN) 
            self.nocoches_sur.wait_for(self.no_car_south)
            self.num_car_north.value += 1
            self.max_coches_norte.value += 1
            self.cochesN_waiting.value -= 1
            self.max_coches_sur.value = 0
            self.muchos_cochesS.notify_all()#tenemos que avisar a los coches en dirección contraria de que pueden empezar a pasar.
        else:
            #haremos lo mismo que en el caso del norte pero justo al contrario:
            self.cochesS_waiting.value += 1
            if self.cochesN_waiting.value != 0:
                self.muchos_cochesS.wait_for(self.demasiados_cochesS)
            self.nocoches_norte.wait_for(self.no_car_north)
            self.num_car_south.value += 1
            self.max_coches_sur.value += 1
            self.cochesS_waiting.value -= 1
            self.max_coches_norte.value = 0
            self.muchos_cochesN.notify_all()
        self.max_coches.value += 1
        self.max_peatones.value = 0 #como pasa un coche al puente, podemos poner el número de peatones seguidos a 0.
        self.muchos_peatones.notify_all()
        self.coches_waiting.value -= 1
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
        return self.max_peatones.value < 5 
    
    #esta no cambia con respecto a la versión anterior:
    def wants_enter_pedestrian(self) -> None:
        self.mutex.acquire()
        self.peat_waiting.value += 1
        if self.coches_waiting.value != 0: 
            self.muchos_peatones.wait_for(self.demasiados_peatones)
        self.nocoches.wait_for(self.no_cars)
        self.num_ped.value += 1
        self.max_peatones.value += 1
        self.max_coches.value = 0
        self.muchos_coches.notify_all()
        self.peat_waiting.value -= 1
        self.peat_en_total.value += 1
        self.mutex.release()

    def leaves_pedestrian(self) -> None:
        self.mutex.acquire()
        self.num_ped.value -= 1
        self.nopeatones.notify_all()
        self.mutex.release()

    def __repr__(self) -> str:
        return f'Peatones: {self.peat_en_total.value}, Coches: {self.coches_en_total.value}, Peatones esperando: {self.peat_waiting.value}, CochesN esperando: {self.cochesN_waiting.value}, CochesS esperando: {self.cochesS_waiting.value}'

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

