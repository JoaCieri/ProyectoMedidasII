import logging
import time
from ut61eplus import UT61EPLUS

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.CRITICAL)

dmm = UT61EPLUS()

print("name=", dmm.getName())
#dmm.sendCommand("lamp")  # enciende la lámpara (opcional)

# iterar 5 veces, con una pausa de 1 segundo entre lecturas
for i in range(5):
    m = dmm.takeMeasurement() #dmm (Digital MultiMeter) es la variable donde el script escupe todo
    print(f"Medición {i+1}: {m}")
    print("\n----------\n")
    time.sleep(2)  # espera 1 segundo
