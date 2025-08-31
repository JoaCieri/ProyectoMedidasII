from serial.tools import list_ports

ports = list_ports.comports()
if not ports:
    print("No hay puertos COM detectados.")
else:
    for p in ports:
        print("-----")
        print("Device:", p.device)              # COMx
        print("Name:", p.name)
        print("Description:", p.description)
        print("HWID:", p.hwid)                  # VID/PID/Serial
        print("Manufacturer:", p.manufacturer)
        print("Product:", p.product)
        print("Serial number:", p.serial_number)