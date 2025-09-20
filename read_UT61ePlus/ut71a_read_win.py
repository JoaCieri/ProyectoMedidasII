import argparse
import time
import sys

try:
    import hid  # paquete 'hidapi'
except Exception as e:
    print("Falta el paquete 'hidapi'. Instalá con: py -m pip install hidapi")
    sys.exit(1)


DEFAULT_CANDIDATES = {
    (0x1A86, 0xE429),  # WCH (muchos cables ópticos Unit aparecen así)
    (0x10C4, 0xEA80),  # Silicon Labs CP2110 (hid-to-uart)
}


def hexdump(bs: bytes) -> str:
    return " ".join(f"{b:02X}" for b in bs)


def asciidump(bs: bytes) -> str:
    return "".join(chr(b) if 32 <= b <= 126 else "." for b in bs)


def find_candidates(vid=None, pid=None):
    devs = list(hid.enumerate())
    items = []
    for d in devs:
        v = d["vendor_id"]; p = d["product_id"]
        mf = d.get("manufacturer_string") or ""
        prod = d.get("product_string") or ""
        ok = False
        if vid is not None and pid is not None:
            ok = (v == vid and p == pid)
        else:
            ok = (v, p) in DEFAULT_CANDIDATES or \
                 "silicon" in mf.lower() or "cp211" in prod.lower() or \
                 "wch" in mf.lower()
        if ok:
            items.append(d)
    return items


def open_by_path(path):
    # Compat: pyhidapi y hidapi
    if hasattr(hid, "Device"):
        return hid.Device(path=path)
    dev = hid.device()
    dev.open_path(path)
    return dev


def main():
    ap = argparse.ArgumentParser(description="Lector HID para UT71A/UNIT – imprime HEX y ASCII.")
    ap.add_argument("--vid", type=lambda x: int(x, 16), help="VID en hex, ej 1A86")
    ap.add_argument("--pid", type=lambda x: int(x, 16), help="PID en hex, ej E429")
    ap.add_argument("--index", type=int, default=0, help="Índice si hay varios iguales (default 0)")
    ap.add_argument("--seconds", type=float, default=10.0, help="Tiempo de lectura (s)")
    ap.add_argument("--csv", type=str, default=None, help="Archivo CSV para guardar (opcional)")
    ap.add_argument("--timeout-ms", type=int, default=500, help="Timeout de lectura (ms)")
    args = ap.parse_args()

    cands = find_candidates(args.vid, args.pid)
    if not cands:
        print("No encontré ningún HID compatible.")
        print("Tip: conectá el multímetro en modo PC/SEND y probá con --vid/--pid.")
        # Mostrar todo lo que ve hid.enumerate para ayudar
        print("\n=== HID enumerados ===")
        for d in hid.enumerate():
            print(f"VID:PID={d['vendor_id']:04X}:{d['product_id']:04X}  "
                  f"mf='{d.get('manufacturer_string','')}'  prod='{d.get('product_string','')}'  path={d.get('path')}")
        sys.exit(2)

    idx = min(max(args.index, 0), len(cands) - 1)
    d = cands[idx]
    path = d["path"]
    print(f"Abriendo: VID:PID={d['vendor_id']:04X}:{d['product_id']:04X}  "
          f"mf='{d.get('manufacturer_string','')}' prod='{d.get('product_string','')}'")
    print(f"path={path}")

    dev = open_by_path(path)
    # No todos soportan set_nonblocking; si falla, omitilo
    try:
        dev.set_nonblocking(1)
    except Exception:
        pass

    csvf = None
    if args.csv:
        csvf = open(args.csv, "w", encoding="utf-8", newline="")
        csvf.write("timestamp,hex,ascii\n")

    print(f"Leyendo {args.seconds}s…  Ctrl+C para salir")
    t0 = time.time()
    try:
        while time.time() - t0 < args.seconds:
            data = dev.read(64, timeout_ms=args.timeout_ms)
            if data:
                ts = time.time()
                hexs = hexdump(bytes(data))
                asci = asciidump(bytes(data))
                print(f"{ts:.3f}  HEX: {hexs}   ASCII: {asci}")
                if csvf:
                    csvf.write(f"{ts:.3f},{hexs},{asci}\n")
            else:
                time.sleep(0.02)
    except KeyboardInterrupt:
        pass
    finally:
        try:
            dev.close()
        except Exception:
            pass
        if csvf:
            csvf.close()
        print("Listo.")

if __name__ == "__main__":
    main()
