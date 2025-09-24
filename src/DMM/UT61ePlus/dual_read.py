import os, sys, json, threading, time, re
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

# --- sync primitives ---
start_barrier = threading.Barrier(2)   # arranque de medición (ambos juntos)
end_barrier   = threading.Barrier(2)   # fin de medición/print (ambos juntos)
print_lock    = threading.Lock()       # evitar mezcla de líneas en consola

def save_buffer_json(buffer, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(list(buffer), f, ensure_ascii=False, indent=2)

# =============== KEITHLEY 2110 ===============
def reader_keithley(n_reads=DEFAULT_READS, interval=DEFAULT_INTERVAL):
    import pyvisa
    buffer = deque(maxlen=BUF_MAXLEN)

    rm = pyvisa.ResourceManager()
    resources = rm.list_resources()
    pick = next((r for r in resources if "2110" in r or "0x05E6" in r or "USB" in r),
                (resources[0] if resources else None))
    if not pick:
        with print_lock:
            print("[KEITHLEY] No hay recursos VISA disponibles.")
        return

    inst = rm.open_resource(pick)
    inst.timeout = 5000
    inst.read_termination = "\n"
    inst.write_termination = "\n"

    try:
        try:
            idn = inst.query("*IDN?").strip()
            with print_lock:
                print(f"[KEITHLEY] {idn}")
        except Exception:
            pass

        inst.write("*CLS")
        inst.write(":CONF:VOLT:DC")   # DCV
        inst.write(":SAMP:COUN 1")

        for i in range(1, n_reads + 1):
            # — sincronizar inicio del ciclo —
            start_barrier.wait()

            raw = inst.query(":MEAS:VOLT:DC?").strip()
            try:
                value = float(raw)
            except ValueError:
                value = raw
            sample = {
                "ts": datetime.now().isoformat(timespec="seconds"),
                "value": value, "raw": raw,
                "mode": "VDC", "resource": pick
            }

            # imprimir alineado (bloqueado)
            with print_lock:
                print(f"[KEITHLEY] {i:02d} {sample['value']}   V   {sample['mode']}")

            buffer.append(sample)
            save_buffer_json(buffer, KEITHLEY_BUF)

            # — sincronizar fin del ciclo —
            leader = end_barrier.wait()  # un hilo será "líder" (retorna 0)
            if leader == 0:
                time.sleep(interval)     # solo uno duerme y marca el ritmo

        inst.write(":SYST:LOC")
    finally:
        try: inst.close()
        except Exception: pass

# ======== UT61E+ helpers: parse línea en valor/unidad/modo ========
_re_display      = re.compile(r"^display\s*=\s*([^\r\n]+)", re.IGNORECASE | re.MULTILINE)
_re_display_unit = re.compile(r"^display_unit\s*=\s*([^\r\n\[\]]+)", re.IGNORECASE | re.MULTILINE)
_re_mode         = re.compile(r"^mode\s*=\s*([^\r\n]+)", re.IGNORECASE | re.MULTILINE)

def parse_ut_line(raw: str):
    m_val  = _re_display.search(raw)
    m_unit = _re_display_unit.search(raw)
    m_mode = _re_mode.search(raw)
    val  = (m_val.group(1).strip()  if m_val  else raw.strip())
    unit = (m_unit.group(1).strip() if m_unit else "")
    mode = (m_mode.group(1).strip() if m_mode else "AUTO")
    return val, unit, mode

# ===================== UT61E+ =====================
def reader_ut61e(n_reads=DEFAULT_READS, interval=DEFAULT_INTERVAL):
    from ut61eplus import UT61EPLUS
    dmm = UT61EPLUS()
    try:
        try:
            with print_lock:
                print(f"[UT61E+] name= {dmm.getName()}")
        except Exception:
            pass

        buffer = deque(maxlen=BUF_MAXLEN)

        for i in range(1, n_reads + 1):
            # — sincronizar inicio del ciclo —
            start_barrier.wait()

            m = dmm.takeMeasurement()
            raw = str(m).strip()
            val, unit, mode = parse_ut_line(raw)

            sample = {
                "ts": datetime.now().isoformat(timespec="seconds"),
                "value": val,
                "raw": f"{val} {unit}".strip(),
                "mode": mode, "resource": "UT61EPLUS"
            }

            with print_lock:
                print(f"[UT61E+]  {i:02d} {val}   {unit}   {mode}")

            buffer.append(sample)
            save_buffer_json(buffer, UT61E_BUF)

            # — sincronizar fin del ciclo —
            leader = end_barrier.wait()
            if leader == 0:
                time.sleep(interval)
    finally:
        try: dmm.close()
        except Exception: pass

# ===================== MAIN =====================
def main():
    with print_lock:
        print(f"[i] Lecturas={DEFAULT_READS}  Intervalo={DEFAULT_INTERVAL}s")

    t1 = threading.Thread(target=reader_keithley, daemon=True)
    t2 = threading.Thread(target=reader_ut61e,   daemon=True)
    t1.start(); t2.start()
    t1.join();  t2.join()

if __name__ == "__main__":
    main()
