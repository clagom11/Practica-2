# Practica-2
En esta práctica hay varios archivos en los que se va resolviendo, de manera gradual, lo que se nos pide en el enunciado:

1. puente_basic.py: en este código lo que se ofrece es una solución sencilla al problema que se nos plantea, sin preocuparnos de evitar inanción, pero 
garantizando la seguridad del puente (no se chocan coches en direcciones contrarias y hay peatones atropellados) y la ausencia de deadlocks.

Los siguientes archivos plantearán soluciones al problema de inanición. La idea consiste, básicamente, en cortar el paso a los coches o peatones en el
caso de que ya hayan pasado muchos de ellos seguidos. Es decir, el programa tendrá unas variables de condición que regularán el paso al puente, como
si hubiera una barrera que se abriese y cerrase para coches y peatones, según la cantidad de ellos seguidos que hayan pasado, para que los demás no se 
queden esperando para siempre. Vemos más detalladamente que hace cada uno de ellos:

2. puente_version1: aquí se presenta una primera solución al problema de inanición, se trata de regular el número de peatones o coches que pasan el puente 
seguidos, de modo que si hay demasiados (coches o peatones) que han pasado de manera continuada (impidiendo el paso de los otros), se les corta el paso, 
para que al menos uno de los otros puedan pasar, y se pueda asegurar que, por tanto, pasarán todos eventualmente.

3. puente_version2: nos damos cuenta de que, a pesar de estar regulando el paso de coches y peatones, dentro de los propios coches se puede producir 
inanción, ya que puede que cuando estén pasando coches, pasen los de una misma dirección continuamente, sin darles lugar a pasar a los de la dirección 
contraria. En este archivo se propone una solución para este problema, que emplea el código de la anterior versión y le añade lo correspondiente para
regular los coches que van en cada dirección, siguiendo una estrategia muy parecida a la de la versión anterior entre coches y peatones, pero esta vez
entre coches que se dirigen al norte o al sur.

Por último, tenemos la parte escrita que se nos pide en el enunciado, con las demostraciones y explicaciones correspondientes:

4. parte escrita puente.pdf: aquí encontramos un pdf en el que hay un pseudo código con la idea básica y con aquella que soluciona los problemas de
inanición por completo, así como demostraciones en todos los casos de que el puente es seguro y no tiene deadlocks, los invariantes que hay y la 
demostración de que la versión "avanzada" resuelve los problemas de inanici
