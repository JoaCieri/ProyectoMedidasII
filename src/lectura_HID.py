import hid

devs = list(hid.enumerate())
print("Total HID:", len(devs))
for d in devs:
    vid = f"{d['vendor_id']:04X}"
    pid = f"{d['product_id']:04X}"
    print(vid, pid, d.get('manufacturer_string'), d.get('product_string'),
          d.get('serial_number'))