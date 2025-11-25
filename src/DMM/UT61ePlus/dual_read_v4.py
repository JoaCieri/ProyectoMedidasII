# dual_read_v4.py
import threading, time, re
from statistics import mean

# ===== VECTORES GLOBALES =====
KEI_VEC, KEI_UNITS = [], []
UT_VEC,  UT_UNITS  = [], []

# ======= HELPERS =======
def _mean_safe(vals):
    nums = [v for v in vals if isinstance(v, (int, float))]
    return mean(nums) if nums else float("nan")

def promedio_keithley():
    return _mean_safe(KEI_VEC)

def promedio_ut61e():
    return _mean_safe(UT_VEC)

def _safe_close(dmm):
    try:
        if hasattr(dmm, "close") and callable(dmm.close):
            dmm.close()
        elif hasattr(dmm, "hid") and hasattr(dmm.hid, "close"):
            dmm.hid.close()
        elif hasattr(dmm, "dev") and hasattr(dmm.dev, "close"):
            dmm.dev.close()
    except Exception:
        pass

# ======= UT61E+ =======
def reader_ut61e(n_reads=10, interval=1.0):
    # import robusto del driver
    try:
        from .ut61eplus import UT61EPLUS
    except Exception:
        from DMM.UT61ePlus.ut61eplus import UT61EPLUS

    re_display = re.compile(r"display\s*=\s*([^\r\n]+)", re.I)
    re_unit    = re.compile(r"display_unit\s*=\s*([^\r\n\[\]]+)", re.I)
    re_mode    = re.compile(r"mode\s*=\s*([^\r\n]+)", re.I)

    def parse(raw):
        m_val  = re_display.search(raw)
        m_unit = re_unit.search(raw)
        m_mode = re_mode.search(raw)
        try:
            val = float(m_val.group(1).strip()) if m_val else float("nan")
        except Exception:
            # por si viene con coma, etc.
            txt = (m_val.group(1).strip() if m_val else "").replace(",", ".")
            val = float(txt) if txt else float("nan")
        unit = m_unit.group(1).strip() if m_unit else ""
        mode = m_mode.group(1).strip() if m_mode else "AUTO"
        return val, unit, mode

    dmm = UT61EPLUS()
    try:
        UT_VEC.clear(); UT_UNITS.clear()
        for _ in range(n_reads):
            raw = str(dmm.takeMeasurement()).strip()
            val, unit, mode = parse(raw)
            UT_VEC.append(val)
            UT_UNITS.append(unit or "V")   # por si el driver no trae unidad
            print(f"[UT61E+] {val:10.5f} {unit:>4}  ({mode})")
            time.sleep(interval)
    finally:
        _safe_close(dmm)

# ======= KEITHLEY 2110 (VISA) =======
def _open_keithley_resource():
    """Devuelve (instancia, unidad, modo) o (None, '', '')."""
    try:
        import pyvisa
    except Exception:
        print("[KEITHLEY] pyvisa no está instalado.")
        return None, "", ""
    try:
        rm = pyvisa.ResourceManager()
        # buscá el 2110 entre recursos conectados
        for r in rm.list_resources():
            try:
                inst = rm.open_resource(r, timeout=3000)
                idn = inst.query("*IDN?").strip()
                if "KEITHLEY" in idn.upper() and "2110" in idn:
                    # modo fijo VDC
                    inst.write("SENS:FUNC 'VOLT:DC'")
                    # unidad usada para imprimir
                    return inst, "V", "VDC"
                inst.close()
            except Exception:
                try: inst.close()
                except Exception: pass
                continue
        print("[KEITHLEY] No se encontró un 2110 en VISA.")
        return None, "", ""
    except Exception as e:
        print(f"[KEITHLEY] Error VISA: {e}")
        return None, "", ""

def reader_keithley(n_reads=10, interval=1.0):
    inst, unit, mode = _open_keithley_resource()
    if inst is None:
        KEI_VEC.clear(); KEI_UNITS.clear()
        return

    KEI_VEC.clear(); KEI_UNITS.clear()
    try:
        for _ in range(n_reads):
            # lectura directa (bloqueante breve)
            try:
                # MEAS:VOLT:DC? realiza config/trigger/lectura de una
                val = float(inst.query("MEAS:VOLT:DC?").strip())
            except Exception:
                # plan B: FETCH?
                val = float(inst.query("FETCH?").strip())
            KEI_VEC.append(val)
            KEI_UNITS.append(unit or "V")
            print(f"[KEITHLEY] {val:10.5f} {unit:>4}  ({mode})")
            time.sleep(interval)
    finally:
        try: inst.close()
        except Exception: pass

# ======= COORDINADOR =======
def run_dual(reads=10, interval=1.0):
    """
    Ejecuta ambos lectores en paralelo. Si alguno falla, el otro sigue.
    Devuelve: (KEI_VEC, KEI_UNITS, UT_VEC, UT_UNITS)
    """
    KEI_VEC.clear(); KEI_UNITS.clear()
    UT_VEC.clear();  UT_UNITS.clear()

    t_ut  = threading.Thread(target=reader_ut61e,   args=(reads, interval), daemon=True)
    t_kei = threading.Thread(target=reader_keithley, args=(reads, interval), daemon=True)

    t_ut.start()
    t_kei.start()
    t_ut.join()
    t_kei.join()

    return KEI_VEC, KEI_UNITS, UT_VEC, UT_UNITS
