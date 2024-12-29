import os
import psutil
import platform
from tabulate import tabulate
import subprocess
from ctypes import *
from ctypes.util import find_library
import cpuinfo

class NVMLWrapper:
    def __init__(self):
        self.nvml_lib = None
        self.load_nvml_library()

    def load_nvml_library(self):
        nvml_path = find_library("nvidia-ml")
        if nvml_path is None:
            raise RuntimeError("NVML library not found. Ensure NVIDIA drivers are installed.")
        self.nvml_lib = CDLL(nvml_path)
        self.nvml_lib.nvmlInit_v2()

    def get_power_usage(self, handle):
        power_usage = c_uint()
        try:
            self.nvml_lib.nvmlDeviceGetPowerUsage(handle, byref(power_usage))
            return power_usage.value / 1000
        except:
            return None

    def list_gpus(self):
        device_count = c_uint()
        self.nvml_lib.nvmlDeviceGetCount_v2(byref(device_count))
        gpus = []
        for idx in range(device_count.value):
            handle = c_void_p()
            self.nvml_lib.nvmlDeviceGetHandleByIndex_v2(idx, byref(handle))
            name = create_string_buffer(256)
            self.nvml_lib.nvmlDeviceGetName(handle, name, 256)
            memory_info = self.get_memory_info(handle)
            power_limit = self.get_power_limit(handle)
            current_power = self.get_power_usage(handle)
            gpus.append({
                "id": idx,
                "name": name.value.decode(),
                "memory": memory_info["total"] // (1024 ** 2),
                "power_limit": power_limit,
                "power_usage": current_power
            })
        return gpus

    def get_memory_info(self, handle):
        class MemoryInfo(Structure):
            _fields_ = [
                ("total", c_ulonglong),
                ("free", c_ulonglong),
                ("used", c_ulonglong),
            ]
        memory_info = MemoryInfo()
        self.nvml_lib.nvmlDeviceGetMemoryInfo(handle, byref(memory_info))
        return {"total": memory_info.total, "free": memory_info.free, "used": memory_info.used}

    def get_power_limit(self, handle):
        power_limit = c_uint()
        self.nvml_lib.nvmlDeviceGetPowerManagementLimit(handle, byref(power_limit))
        return power_limit.value // 1000

    def set_power_limit(self, handle, limit):
        self.nvml_lib.nvmlDeviceSetPowerManagementLimit(handle, c_uint(limit * 1000))

    def set_memory_frequency(self, handle, freq):
        self.nvml_lib.nvmlDeviceSetApplicationsClocks(handle, freq, freq)

def get_system_info():
    system_info = {
        "OS": platform.system(),
        "Version": platform.version(),
        "Architecture": platform.architecture()[0],
        "CPU": cpuinfo.get_cpu_info()['brand_raw'],
        "Cores": psutil.cpu_count(logical=False),
        "Threads": psutil.cpu_count(logical=True),
        "RAM (Total)": f"{round(psutil.virtual_memory().total / (1024 ** 3), 2)} GB"
    }

    try:
        nvml = NVMLWrapper()
        gpus = nvml.list_gpus()
        print("System Information:")
        print(tabulate(system_info.items(), headers=["Component", "Details"]))
        print("\nGPU Information:")
        gpu_info = []
        total_power = 0
        for gpu in gpus:
            current_power = f"{gpu['power_usage']:.1f} W" if gpu['power_usage'] is not None else "N/A"
            gpu_info.append([
                f"GPU {gpu['id']}: {gpu['name']}",
                f"Memory: {gpu['memory']} MB | Power Limit: {gpu['power_limit']} W | Current Usage: {current_power}"
            ])
            if gpu['power_usage'] is not None:
                total_power += gpu['power_usage']
        print(tabulate(gpu_info, headers=["GPU", "Specifications"]))
        print(f"\nTotal GPU Power Consumption: {total_power:.1f} W")
    except Exception as e:
        print("\nWarning: Could not retrieve GPU information:", str(e))
        print(tabulate(system_info.items(), headers=["Component", "Details"]))

def monitor_resources():
    print("\nMonitoring Resources (Press Ctrl+C to exit):")
    nvml = NVMLWrapper()
    try:
        while True:
            cpu_usage = psutil.cpu_percent(interval=1)
            ram = psutil.virtual_memory()
            gpus = nvml.list_gpus()
            os.system('clear' if os.name == 'posix' else 'cls')
            system_info = [
                ["CPU Usage", f"{cpu_usage} %"],
                ["RAM Usage", f"{ram.used / (1024 ** 3):.2f} GB / {ram.total / (1024 ** 3):.2f} GB"],
            ]
            total_power = 0
            for gpu in gpus:
                current_power = gpu['power_usage']
                if current_power is not None:
                    total_power += current_power
                power_str = f"{current_power:.1f} W" if current_power is not None else "N/A"
                system_info.append([
                    f"GPU {gpu['id']} Power",
                    power_str
                ])
            system_info.append(["Total GPU Power", f"{total_power:.1f} W"])
            print("Resource Usage:")
            print(tabulate(system_info, headers=["Resource", "Usage"]))
    except KeyboardInterrupt:
        print("\nExiting resource monitoring.")

def configure_gpu():
    nvml = NVMLWrapper()
    gpus = nvml.list_gpus()
    print("Available GPUs:")
    for gpu in gpus:
        print(f"{gpu['id'] + 1}. {gpu['name']} (Memory: {gpu['memory']} MB, Power Limit: {gpu['power_limit']} W)")
    choice = int(input("Select GPU to configure (number): ")) - 1
    if 0 <= choice < len(gpus):
        gpu = gpus[choice]
        handle = c_void_p()
        nvml.nvml_lib.nvmlDeviceGetHandleByIndex_v2(gpu['id'], byref(handle))
        mem_freq_input = input("Set memory frequency in MHz (press Enter to keep current): ").strip()
        if mem_freq_input:
            try:
                mem_freq = int(mem_freq_input)
                nvml.set_memory_frequency(handle, mem_freq)
                print(f"Memory Frequency updated to {mem_freq} MHz")
            except ValueError:
                print("Invalid memory frequency value. Keeping current setting.")
        else:
            print("Keeping current memory frequency setting")
        power_limit_input = input("Set power limit in W (press Enter to keep current): ").strip()
        if power_limit_input:
            try:
                power_limit = int(power_limit_input)
                nvml.set_power_limit(handle, power_limit)
                print(f"Power limit updated to {power_limit} W")
            except ValueError:
                print("Invalid power limit value. Keeping current setting.")
        else:
            print("Keeping current power limit setting")
        print(f"\nConfiguration complete for {gpu['name']}")
    else:
        print("Invalid selection.")

def main():
    while True:
        print("\nMining Rig Management Tool")
        print("1. View System Information")
        print("2. Monitor Resource Usage")
        print("3. Configure GPU Settings")
        print("4. Exit")
        choice = input("Enter your choice: ")
        if choice == "1":
            get_system_info()
        elif choice == "2":
            monitor_resources()
        elif choice == "3":
            configure_gpu()
        elif choice == "4":
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()

