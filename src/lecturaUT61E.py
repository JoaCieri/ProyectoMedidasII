# test_hid.py
import hid

devs = [d for d in hid.enumerate() if d['vendor_id']==0x10C4 and d['product_id']==0xEA80]
print("CP2110 encontrados:", len(devs))
for d in devs:
    print(d.get('product_string'), d.get('serial_number'), d.get('path'))