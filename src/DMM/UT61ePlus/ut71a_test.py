import json, time, argparse, re, threading, hid
from collections import Counter, deque

VID, PID = 0x1A86, 0xE429
MAP_FILE = "ut71a_map.json"

# bytes que más cambian en tu dump (ajustable si hace falta)
FIELD_SLICE = slice(1, 9)      # 1..8
STABLE_FRAMES = 8              # cuántos frames iguales consideramos "estable"

def find_path():
    for d in hid.enumerate():
        if d['vendor_id'] == VID and d['product_id'] == PID:
            return d['path'], d
    return None, None

def hexd(bs): return " ".join(f"{b:02X}" for b in bs)

def load_map():
    try:
        with open(MAP_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"digits": [{} for _ in range(FIELD_SLICE.stop-FIELD_SLICE.start)],
                "units": {}, "dp": {}}

def save_map(m):
    with open(MAP_FILE, "w", encoding="utf-8") as f:
        json.dump(m, f, indent=2)

def split_numeric_units(s):
    s = s.strip()
    m = re.match(r"^([+-]?\d+(?:\.\d+)?)(?:\s*([a-zA-ZΩµu%]+))?$", s)
    if not m: return None, None
    return m.group(1), (m.group(2) or "")

def majority_bytes(frames):
    cols = list(zip(*frames))
    return bytes(Counter(col).most_common(1)[0][0] for col in cols)

def reader_thread(dev, out_state):
    """Lee siempre (keep-alive) y mantiene la ventana de frames recientes por patrón."""
    dev.set_nonblocking(1)
    last = None
    buf_by_key = {}  # key -> deque of lists
    while not out_state["stop"]:
        d = dev.read(64, timeout_ms=50)  # leer SIEMPRE
        if not d:
            continue
        key = bytes(d[FIELD_SLICE])
        if key not in buf_by_key:
            buf_by_key[key] = deque(maxlen=32)
        buf_by_key[key].append(list(key))
        # detectar cambios
        if last is None or key != last:
            out_state["changed"] = True
        last = key
        out_state["last_key"] = key
        out_state["buffers"] = buf_by_key

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seconds", type=float, default=90.0,
                    help="tiempo total de aprendizaje")
    args = ap.parse_args()

    path, meta = find_path()
    if not path:
        print("No encontré 1A86:E429. Poné el UT71A en PC/SEND y reconectá.")
        return

    print(f"Abrir: VID:PID={meta['vendor_id']:04X}:{meta['product_id']:04X}  "
          f"mf='{meta.get('manufacturer_string')}' prod='{meta.get('product_string')}'")

    dev = hid.Device(path=path) if hasattr(hid, "Device") else hid.device(); \
          (dev.open_path(path) if not hasattr(hid, "Device") else None)

    learn = load_map()

    state = {"stop": False, "last_key": None, "buffers": {}, "changed": False}
    t = threading.Thread(target=reader_thread, args=(dev, state), daemon=True)
    t.start()

    print("Aprendiz con keep-alive.\n"
          "- Consejo: usá HOLD para congelar la lectura mientras tipeás.\n"
          "- Ingresá valores como '12.34 mV', '0.000 V', '1.000 kΩ'.\n"
          "- Enter vacío salta.\n")

    t0 = time.time()
    last_shown = None
    try:
        while time.time() - t0 < args.seconds:
            key = state["last_key"]
            if not key:
                time.sleep(0.05); continue

            # ¿está estable?
            buf = state["buffers"].get(key, deque())
            if len(buf) >= STABLE_FRAMES:
                # si cambió y no mostramos este patrón, ofrecer etiquetar
                if state["changed"] or key != last_shown:
                    patt = majority_bytes(buf)
                    print("\nPatrón:", hexd(patt))
                    txt = input("¿Qué ves (ej: '12.34 mV')? (Enter salta) > ").strip()
                    state["changed"] = False
                    last_shown = key
                    if not txt:
                        continue
                    num, unit = split_numeric_units(txt)
                    if num is None:
                        print("Formato no reconocido. Probá '12.34 mV'.")
                        continue

                    # posición del punto desde la derecha
                    dp_from_right = 0
                    if "." in num:
                        dp_from_right = len(num) - num.rfind(".") - 1
                    digits_only = num.replace(".", "")

                    slots = FIELD_SLICE.stop - FIELD_SLICE.start
                    padded = digits_only[-slots:].rjust(slots, " ")

                    for i, (b, ch) in enumerate(zip(patt, padded)):
                        if ch.isdigit():
                            learn["digits"][i][f"{b:02X}"] = ch

                    hexkey = "".join(f"{b:02X}" for b in patt)
                    learn["dp"][hexkey] = dp_from_right
                    learn["units"][hexkey] = unit
                    save_map(learn)
                    print("Guardado en", MAP_FILE)
            else:
                time.sleep(0.05)
    finally:
        state["stop"] = True
        try: dev.close()
        except: pass

if __name__ == "__main__":
    main()
