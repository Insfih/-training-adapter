from pathlib import Path

VENDORS = {
    "0x8086": "Intel",
    "0x10de": "NVIDIA",
    "0x1002": "AMD",
    "0x1022": "AMD",
    "0x102b": "Matrox",
    "0x1a03": "ASPEED",
    "0x1234": "QEMU (стандартная виртуальная VGA)",
    "0x1af4": "Red Hat (virtio-gpu)",
    "0x15ad": "VMware",
    "0x80ee": "VirtualBox",
    "0x1414": "Microsoft (Hyper-V)",
}

dev = Path('/sys/bus/pci/devices/0000:00:02.0')
print((dev / 'vendor').read_text().strip())
print((dev / 'device').read_text().strip())
print((dev / 'class').read_text().strip())

def type_GPU() -> None:
    dev = Path('/sys/bus/pci/devices/0000:00:02.0')
    for id in VENDORS:
        if id in (dev / 'vendor').read_text().strip():
            print(VENDORS[id])
            break

def cpuinfo_to_dict() -> dict:
    data_text = Path("/proc/cpuinfo").read_text()
    data_mas = (data_text.replace('\t', '')).split('\n')
    data_dict = {}
    for row in data_mas:
        row = row.split(': ')
        data_dict[row[0]] = row[-1]
    return data_dict

def cpu_manufacturer() -> str:
    cpuinfo_file = cpuinfo_to_dict()
    if 'intel' in cpuinfo_file['model name'].lower() or 'intel' in cpuinfo_file['vendor_id'].lower():
        return 'Intel'
    elif 'amd' in cpuinfo_file['model name'].lower() or 'amd' in cpuinfo_file['vendor_id'].lower():
        return 'AMD'
    else:
        return 'unknown'

def id_dir_pci() -> str:




def discret(cpu_manufacturer):
    if cpu_manufacturer == 'Intel':

    elif cpu_manufacturer == 'AMD':

    else:
        return 0

print(Path('/sys/class/drm/cardN/device/mem_info_vram_total').read_text())