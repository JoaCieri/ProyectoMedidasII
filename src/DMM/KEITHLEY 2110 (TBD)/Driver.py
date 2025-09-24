# keithley_buffer.py
# Requisitos: pip install pyvisa
# Uso directo (demo):  py keithley_buffer.py
# Uso como módulo: from keithley_buffer import read_dcv_to_buffer, load_buffer

import os, json, time
from datetime import datetime
from collections import deque
import pyvisa

# ----- Config por defecto -----
READS_DEFAULT = 10          # cuántas mediciones tomar
INTERVAL_DEFAULT = 1.0      # segundos entre lecturas
BUF_MAXLEN = 10           # tamaño max del buffer (anillo)
BUF_PATH_DEFAULT = os.path.join(os.path.expanduser("~"), "Desktop", "Driver.json")

# ----- Buffer en memoria (para cuando se usa como módulo) -----
_buffer = deque(maxlen=BUF_MAXLEN)

def _save_buffer_json(path=BUF_PATH_DEFAULT):
    """Guarda el buffer completo a JSON (timestamp ISO + valor)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(list(_buffer), f, ensure_ascii=False, indent=2)

def load_buffer(path=BUF_PATH_DEFAULT):
    """Carga (solo lectura) el buffer desde JSON. Devuelve lista de dicts."""
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _open_instrument(preferred=None):
    rm = pyvisa.ResourceManager()
    resources = rm.list_resources()
    # Elegimos el recurso preferido si lo pasaron; si no, uno probable/primero.
    if preferred:
        inst = rm.open_resource(preferred)
    else:
        pick = next((r for r in resources if "2110" in r or "0x05E6" in r or "USB" in r), None)
        if not pick and resources:
            pick = resources[0]
        if not pick:
            raise RuntimeError("No hay recursos VISA disponibles.")
        inst = rm.open_resource(pick)
    inst.timeout = 5000
    inst.read_termination = "\n"
    inst.write_termination = "\n"
    return inst

def read_dcv_to_buffer(resource_str=None, n_reads=READS_DEFAULT, interval=INTERVAL_DEFAULT,
                       buf_path=BUF_PATH_DEFAULT, return_list=True):
    """
    Lee DCV del Keithley 2110, imprime en pantalla y guarda cada muestra en un buffer persistente (JSON).
    - resource_str: nombre VISA (si None intenta detectar)
    - n_reads: cantidad de lecturas
    - interval: segundos entre lecturas
    - buf_path: ruta del JSON donde persiste el buffer (default: Desktop\KEITHLEY_BUFFER.json)
    - return_list: si True devuelve la lista (copiada) con lo leído en esta corrida

    Devuelve: lista de dicts [{'ts': ISO8601, 'value': float|str, 'raw': '...'}] de ESTA sesión.
    """
    session_samples = []
    inst = _open_instrument(resource_str)

    try:
        # Configurar DCV
        inst.write("*CLS")
        inst.write(":CONF:VOLT:DC")
        inst.write(":SAMP:COUN 1")

        print(f"[i] Tomando {n_reads} mediciones DCV, cada {interval}s. Ctrl+C para abortar.\n")

        for i in range(1, n_reads + 1):
            raw = inst.query(":MEAS:VOLT:DC?").strip()
            try:
                value = float(raw)
            except ValueError:
                value = raw  # por si el equipo devuelve "12.345 VDC" u otro formato

            sample = {
                "ts": datetime.now().isoformat(timespec="seconds"),
                "value": value,
                "raw": raw
            }
            # Mostrar en consola
            print(f"{i:02d} {sample['ts']}  {sample['raw']}")

            # Guardar en buffer en memoria y persistir a disco
            _buffer.append(sample)
            session_samples.append(sample)
            _save_buffer_json(buf_path)

            time.sleep(interval)

        print("\n[i] Devolviendo control al panel frontal (LOCAL).")
        inst.write(":SYST:LOC")

    finally:
        try:
            inst.close()
        except Exception:
            pass

    return session_samples if return_list else None

# --- Demo si se ejecuta directo ---
if __name__ == "__main__":
    read_dcv_to_buffer(n_reads=10, interval=1.0)
    print(f"[i] Buffer guardado en: {BUF_PATH_DEFAULT}")
