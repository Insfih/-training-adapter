from pathlib import Path

# Словарь: PCI Vendor ID -> название производителя.
# Используется для перевода числового идентификатора из /sys/bus/pci/devices/*/vendor
# в человекочитаемое имя (реальные GPU и виртуальные видеоадаптеры гипервизоров).
g_mapVendors = {
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
# Каталог sysfs, в котором ядро Linux перечисляет все PCI-устройства
g_strDevicesPath = '/sys/bus/pci/devices'
# Файл с информацией о процессоре
g_strCpuinfoPath = '/proc/cpuinfo'


def cpuinfo_to_dict() -> dict:
    """
    Читает /proc/cpuinfo и превращает его в словарь {параметр: значение},
    например {'vendor_id': 'GenuineIntel', 'model name': 'Intel(R) Core(TM) ...', ...}.

    Убирает символы табуляции, разбивает текст на строки, а каждую строку —
    по разделителю ': ' на ключ и значение.
    Замечание по поведению: /proc/cpuinfo содержит блок для каждого ядра,
    поэтому одинаковые ключи перезаписываются и в словаре остаются значения
    последнего ядра. Пустые строки дают ключ '' со значением ''.
    """
    strCpuinfoText = Path(g_strCpuinfoPath).read_text()
    # Удаляем табуляции (в cpuinfo они стоят между ключом и двоеточием) и делим на строки
    vstrCpuinfoRows = (strCpuinfoText.replace('\t', '')).split('\n')
    mapCpuinfo = {}
    for strRow in vstrCpuinfoRows:
        vstrKeyValue = strRow.split(': ')
        # Первый элемент — ключ, последний — значение
        # (если ': ' нет, ключ и значение совпадут)
        mapCpuinfo[vstrKeyValue[0]] = vstrKeyValue[-1]
    return mapCpuinfo


def cpu_manufacturer() -> str:
    """
    Определяет производителя процессора: 'Intel', 'AMD' или 'unknown'.

    Смотрит поля 'model name' и 'vendor_id' из /proc/cpuinfo
    (vendor_id обычно 'GenuineIntel' или 'AuthenticAMD')
    и ищет в них подстроки 'intel' / 'amd' без учёта регистра.
    """
    mapCpuinfo = cpuinfo_to_dict()
    if 'intel' in mapCpuinfo['model name'].lower() or 'intel' in mapCpuinfo['vendor_id'].lower():
        return 'Intel'
    elif 'amd' in mapCpuinfo['model name'].lower() or 'amd' in mapCpuinfo['vendor_id'].lower():
        return 'AMD'
    else:
        return 'unknown'

def gpu_manufacturer(pthDev: Path) -> str:
    for strVendorId in g_mapVendors:
        # Сравниваем Vendor ID из словаря с содержимым файла vendor
        if strVendorId in (pthDev / 'vendor').read_text().strip():
            return g_mapVendors[strVendorId]
    return 'unknown'

def intel_discret(pthDev: Path) -> bool:
    """ 
    проверка является ли Intel видеоадаптер дискретным
    """
    bDiscretGPU = Path(f"{pthDev}/current_link_speed").is_file() and Path(f"{pthDev}/max_link_width").is_file()
    return bDiscretGPU

def AMD_discret(pthDev: Path) -> bool:
    bDiscretGPU = False
    if Path(f"{pthDev}/mem_info_vram_total").is_file():
        bDiscretGPU = int(Path(f"{pthDev}/mem_info_vram_total").read_text()) > 512 * 1024 * 1024
    
    return bDiscretGPU

def isnt_discrete(pthDev: Path) -> bool:
    """
    Заготовка (пока не реализована) для определения, является ли видеокарта дискретной,
    с учётом производителя процессора.

    Текущее поведение: для 'Intel' и 'AMD' ничего не делает и возвращает None,
    для любого другого значения возвращает 0.
    """
    if cpu_manufacturer() == 'Intel' and gpu_manufacturer(pthDev) == 'Intel' and not intel_discret(pthDev):
        return 1
    elif cpu_manufacturer() == 'AMD' and gpu_manufacturer(pthDev) == 'AMD' and int(Path(f"{pthDev}/mem_info_vram_total").read_text()) <= 512 * 1024 * 1024:
        return 1
    else:
        return 0
    
def gpu_pci_dir_names() -> list:
    """
    Возвращает список имён PCI-устройств (вида '0000:00:02.0'),
    которые являются видеоадаптерами.

    Перебирает все каталоги в /sys/bus/pci/devices и читает файл class.
    PCI-класс 0x03xxxx означает "Display controller" (VGA, 3D-контроллер и т.п.),
    поэтому если в содержимом class есть подстрока '0x03' — устройство считается GPU.
    """
    vstrPciDirNames = []
    for pthPciDir in Path('/sys/bus/pci/devices').iterdir():
        # Каталог устройства + его класс начинается с 0x03 (дисплейный контроллер)
        if pthPciDir.is_dir() and '0x03' in Path(f'{pthPciDir}/class').read_text():
            vstrPciDirNames.append(pthPciDir.name)
    return vstrPciDirNames


def gpu_pci_dir_paths() -> list:
    """
    Возвращает список полных путей (Path) к каталогам видеоадаптеров в sysfs,
    например Path('/sys/bus/pci/devices/0000:00:02.0').

    Берёт имена из gpu_pci_dir_names() и приклеивает к ним g_strDevicesPath.
    """
    vpthPciDirPaths = []
    for strPciDirName in gpu_pci_dir_names():
        vpthPciDirPaths.append(Path(g_strDevicesPath + '/' + strPciDirName))
    return vpthPciDirPaths

def gpu_vendor_names() -> list:
    """
    Возвращает список названий производителей для всех найденных видеоадаптеров
    (в том же порядке, что и gpu_pci_dir_paths()).

    Например: ['Intel', 'NVIDIA'] на ноутбуке с гибридной графикой.
    Для неизвестных производителей в списке будет None.
    """
    vstrGpuVendors = []
    for pthPciDir in gpu_pci_dir_paths():
        vstrGpuVendors.append(gpu_manufacturer(pthPciDir))
    return vstrGpuVendors


# --- Отладочный вывод ---
# Список PCI-имён всех найденных видеоадаптеров
print(gpu_pci_dir_names())
# Берём первый найденный GPU (упадёт с IndexError, если GPU нет)
pthFirstGpu = Path(gpu_pci_dir_paths()[0])
# Vendor ID производителя, например 0x10de
print((pthFirstGpu / 'vendor').read_text().strip())
# Device ID конкретной модели устройства
print((pthFirstGpu / 'device').read_text().strip())
# PCI-класс устройства, например 0x030000 (VGA-совместимый контроллер)
print((pthFirstGpu / 'class').read_text().strip())