# dual_read.py
# Ejecutar:  py .\dual_read.py  [lecturas] [intervalo_s]
# Ej:        py .\dual_read.py          -> 10 lecturas, 1 s
#            py .\dual_read.py 20 0.5   -> 20 lecturas, 0.5 s
#
# Requisitos:
#   pip install pyvisa
#   (y tu paquete/archivo que provee UT61EPLUS)

import os, sys, json, time, threading
from collections import deque
from datetime import datetime

# ----- CONFIG -----
DEFAULT_READS = int(sys.argv[1]) if len(sys.argv) > 1 else 10
DEFAULT_INTERVAL = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
BUF_MAXLEN = 1000

DESKTOP = os.path.join(os.path.expanduser("~"), "Desktop")
KEITHLEY_BUF = os.path.join(DESKTOP, "KEITHLEY_BUFFER.json")
UT61E_BUF     = os.path.join(DESKTOP, "UT61EPLUS_BUFFER.json")
# -------------------

# ---------- Utilidades buffer ----------
def save_buffer_json(buffer, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(list(buffer), f, ensure_ascii=False, indent=2)

def load_buffer_json(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
# --------------------------------------

# ---------- Hilo KEITHLEY 2110 ----------
def reader_keithley(n_reads=DEFAULT_READS, interval=DEFAULT_INTERVAL):
    import pyvisa  # local para no requerirlo si solo usás UT
    buffer = deque(maxlen=BUF_MAXLEN)

    # Abrir recurso (auto-pick)
    rm = pyvisa.ResourceManager()
    resources = rm.list_resources()
    pick = next((r for r in resources if "2110" in r or "0x05E6" in r or "USB" in r), (resources[0] if resources else None))
    if not pick:
        print("[KEITHLEY] No hay recursos VISA disponibles.")
        return

    inst = rm.open_resource(pick)
    inst.timeout = 5000
    inst.read_termination = "\n"
    inst.write_termination = "\n"

    try:
        try:
            idn = inst.query("*IDN?").strip()
            print(f"[KEITHLEY] {idn}")
        except Exception:
            pass

        inst.write("*CLS")
        inst.write(":CONF:VOLT:DC")   # DCV
        inst.write(":SAMP:COUN 1")

        for i in range(1, n_reads + 1):
            raw = inst.query(":MEAS:VOLT:DC?").strip()
            try:
                value = float(raw)
            except ValueError:
                value = raw
            sample = {
                "ts": datetime.now().isoformat(timespec="seconds"),
                "value": value,
                "raw": raw,
                "mode": "VDC",
                "resource": pick,
            }
            print(f"[KEITHLEY] {i:02d} {sample['ts']}  {sample['raw']}")
            buffer.append(sample)
            save_buffer_json(buffer, KEITHLEY_BUF)
            time.sleep(interval)

        inst.write(":SYST:LOC")
    finally:
        try: inst.close()
        except Exception: pass

# ---------- Hilo UT61E+ ----------
def reader_ut61e(n_reads=DEFAULT_READS, interval=DEFAULT_INTERVAL):
    # Importá tu clase tal como la usás en readDMM.py
    from ut61eplus import UT61EPLUS
    dmm = UT61EPLUS()
    try:
        try:
            print(f"[UT61E+] name= {dmm.getName()}")
        except Exception:
            pass

        buffer = deque(maxlen=BUF_MAXLEN)

        for i in range(1, n_reads + 1):
            m = dmm.takeMeasurement()       # objeto Measurement (str() ya formatea)
            raw = str(m).strip()
            # Opcional: si querés además extraer solo valor numérico/unidad, parsealo aquí.
            sample = {
                "ts": datetime.now().isoformat(timespec="seconds"),
                "value": raw,                # dejamos el string completo
                "raw": raw,
                "mode": "AUTO",              # o el modo que exponga tu lib
                "resource": "UT61EPLUS",
            }
            print(f"[UT61E+]  {i:02d} {sample['ts']}  {sample['raw']}")
            buffer.append(sample)
            save_buffer_json(buffer, UT61E_BUF)
            time.sleep(interval)
    finally:
        try:
            dmm.close()
        except Exception:
            pass

# ---------- MAIN ----------
def main():
    print(f"[i] Lecturas={DEFAULT_READS}  Intervalo={DEFAULT_INTERVAL}s")
    t1 = threading.Thread(target=reader_keithley, daemon=True)
    t2 = threading.Thread(target=reader_ut61e,   daemon=True)

    t1.start(); t2.start()
    t1.join();  t2.join()

    # Al terminar, mostrar resumen buffers
    k = load_buffer_json(KEITHLEY_BUF)
    u = load_buffer_json(UT61E_BUF)
    n_show = 10

    print("\n=== ÚLTIMAS mediciones (KEITHLEY) ===")
    for r in k[-n_show:]:
        print(f"[KEITHLEY] {r['ts']}  {r['raw']}  [{r['mode']}]")

    print("\n=== ÚLTIMAS mediciones (UT61E+) ===")
    for r in u[-n_show:]:
        print(f"[UT61E+]  {r['ts']}  {r['raw']}  [{r['mode']}]")

    print(f"\n[i] Buffers:\n  KEITHLEY -> {KEITHLEY_BUF}\n  UT61E+   -> {UT61E_BUF}")

if __name__ == "__main__":
    main()
