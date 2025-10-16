import threading, time, re
from statistics import mean

UT_VEC, UT_UNITS = [], []

def reader_ut61e(n_reads=10, interval=1.0):
    try:
        from .ut61eplus import UT61EPLUS
    except Exception:
        from DMM.UT61ePlus.ut61eplus import UT61EPLUS

    import time, re
    re_display = re.compile(r"display\s*=\s*([^\r\n]+)", re.I)
    re_unit    = re.compile(r"display_unit\s*=\s*([^\r\n\[\]]+)", re.I)
    re_mode    = re.compile(r"mode\s*=\s*([^\r\n]+)", re.I)

    def parse(raw):
        m_val  = re_display.search(raw)
        m_unit = re_unit.search(raw)
        m_mode = re_mode.search(raw)
        val  = float(m_val.group(1).strip()) if m_val else float("nan")
        unit = m_unit.group(1).strip() if m_unit else ""
        mode = m_mode.group(1).strip() if m_mode else "AUTO"
        return val, unit, mode

    dmm = UT61EPLUS()
    try:
        print("----------------------")
        for _ in range(n_reads):
            raw = str(dmm.takeMeasurement()).strip()
            val, unit, mode = parse(raw)
            UT_VEC.append(val)
            UT_UNITS.append(unit)
            print(f"[UT61E+] {val:8.4f} {unit:>5}  ({mode})")
            time.sleep(interval)
    finally:
        # cierre tolerante: llamá a lo que exista y no explotes si no está
        try:
            if hasattr(dmm, "close") and callable(getattr(dmm, "close")):
                dmm.close()
            elif hasattr(dmm, "hid") and hasattr(dmm.hid, "close"):
                dmm.hid.close()
            elif hasattr(dmm, "dev") and hasattr(dmm.dev, "close"):
                dmm.dev.close()
        except Exception:
            pass


def run_dual(reads=10, interval=1.0):
    """Ejecuta el hilo de lectura del UT61E+ y devuelve los vectores."""
    t_ut = threading.Thread(target=reader_ut61e, args=(reads, interval), daemon=True)
    t_ut.start(); t_ut.join()
    return UT_VEC, UT_UNITS

def promedio_valores():
    """Devuelve el promedio de los valores medidos."""
    try:
        return mean(UT_VEC)
    except Exception:
        return float("nan")
