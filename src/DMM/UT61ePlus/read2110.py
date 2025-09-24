# read2110.py
# Uso: py read2110.py [RECURSO_VISA] [MODO] [LECTURAS] [INTERVALO]
# Ejemplos:
#   py read2110.py
#   py read2110.py USB0::0x05E6::0x2110::1234567::INSTR VDC 10 1.0
#
# MODO: VDC | VAC | IDC | IAC | RES | FRES | READ
#
# Requisitos: pip install pyvisa

import os, sys, json, time
from datetime import datetime
from collections import deque
import pyvisa

# ---------------- Config por defecto ----------------
DEFAULT_MODE = "VDC"        # VDC/VAC/IDC/IAC/RES/FRES/READ
DEFAULT_READS = 10          # cuántas mediciones
DEFAULT_INTERVAL = 1.0      # segundos entre mediciones
BUFFER_MAXLEN = 1000        # tamaño del buffer (anillo)
BUFFER_PATH = os.path.join(os.path.expanduser("~"), "Desktop", "KEITHLEY_BUFFER.json")
# ----------------------------------------------------

SCPI_MEAS = {
    "VDC":  (":CONF:VOLT:DC",  ":MEAS:VOLT:DC?"),
    "VAC":  (":CONF:VOLT:AC",  ":MEAS:VOLT:AC?"),
    "IDC":  (":CONF:CURR:DC",  ":MEAS:CURR:DC?"),
    "IAC":  (":CONF:CURR:AC",  ":MEAS:CURR:AC?"),
    "RES":  (":CONF:RES",      ":MEAS:RES?"),
    "FRES": (":CONF:FRES",     ":MEAS:FRES?"),   # 4 hilos (si no soporta, usar RES)
    "READ": (None,             ":READ?"),        # lee según config actual
}

def open_instrument(preferred=None):
    rm = pyvisa.ResourceManager()
    resources = rm.list_resources()
    print("[i] Recursos VISA:", resources)
    if preferred:
        inst = rm.open_resource(preferred)
        picked = preferred
    else:
        picked = next((r for r in resources if "2110" in r or "0x05E6" in r or "USB" in r), None)
        if not picked and resources: picked = resources[0]
        if not picked: raise RuntimeError("No hay recursos VISA disponibles.")
        inst = rm.open_resource(picked)

    inst.timeout = 5000
    inst.read_termination = "\n"
    inst.write_termination = "\n"
    return inst, picked

def save_buffer_json(buffer, path=BUFFER_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(list(buffer), f, ensure_ascii=False, indent=2)
    return path

def load_buffer_json(path=BUFFER_PATH):
    if not os.path.exists(path): return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def main():
    # CLI: recurso, modo, lecturas, intervalo
    preferred = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] not in ("", '""') else None
    mode = (sys.argv[2].upper() if len(sys.argv) > 2 else DEFAULT_MODE)
    n_reads = int(sys.argv[3]) if len(sys.argv) > 3 else DEFAULT_READS
    interval = float(sys.argv[4]) if len(sys.argv) > 4 else DEFAULT_INTERVAL

    if mode not in SCPI_MEAS:
        print(f"[!] Modo '{mode}' no válido. Usando {DEFAULT_MODE}.",
              f"Opciones: {', '.join(SCPI_MEAS)}")
        mode = DEFAULT_MODE

    inst, resource = open_instrument(preferred)

    buffer = deque(maxlen=BUFFER_MAXLEN)

    try:
        # Identificación
        try:
            idn = inst.query("*IDN?").strip()
            print("[i] *IDN?:", idn)
        except Exception:
            pass

        inst.write("*CLS")

        # Configurar modo (si corresponde)
        conf_cmd, read_cmd = SCPI_MEAS[mode]
        if conf_cmd:
            inst.write(conf_cmd)

        inst.write(":SAMP:COUN 1")  # una muestra por lectura

        print(f"[i] Modo: {mode} | Recurso: {resource}")
        print(f"[i] Midiendo {n_reads} lecturas, cada {interval}s. Ctrl+C para abortar.\n")

        for i in range(1, n_reads + 1):
            raw = inst.query(read_cmd).strip()
            try:
                value = float(raw)
            except ValueError:
                value = raw  # si viene con unidad

            sample = {
                "ts": datetime.now().isoformat(timespec="seconds"),
                "value": value,
                "raw": raw,
                "mode": mode,          # <<<<<< guarda el modo
                "resource": resource,
            }

            # mostrar en vivo
            #print(f"{i:02d} {sample['ts']}  {sample['raw']}  [{sample['mode']}]")

            # guardar en buffer (memoria) y persistir a JSON
            buffer.append(sample)
            save_buffer_json(buffer, BUFFER_PATH)

            time.sleep(interval)

        print("\n[i] Finalizado. Pasando a LOCAL…")
        inst.write(":SYST:LOC")

    finally:
        try: inst.close()
        except Exception: pass

    # Leer el JSON y mostrar un resumen del buffer
    data = load_buffer_json(BUFFER_PATH)
    print(f"\n[i] Buffer persistido en: {BUFFER_PATH}")
    print(f"[i] Total muestras en buffer: {len(data)}")
    for row in data[-min(10, len(data)):]:
        print(f"{row['ts']}  {row['raw']}  [{row['mode']}]")

if __name__ == "__main__":
    main()
