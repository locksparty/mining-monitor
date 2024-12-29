import os
import psutil
import platform
from tabulate import tabulate
from ctypes import *
from ctypes.util import find_library
import cpuinfo
import time
import curses

############################################
# Core NVML functionality derived from py-nvtool
############################################

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
            return power_usage.value / 1000  # Convert from milliwatts to watts
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
                "memory": memory_info["total"] // (1024 ** 2),  # Convert to MB
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
        return power_limit.value // 1000  # Convert to watts

    def set_power_limit(self, handle, limit):
        self.nvml_lib.nvmlDeviceSetPowerManagementLimit(handle, c_uint(limit * 1000))

    def set_memory_frequency(self, handle, freq):
        self.nvml_lib.nvmlDeviceSetApplicationsClocks(handle, freq, freq)

############################################
# Main Script Functionality
############################################

def get_system_info():
    """Collect and display basic system information."""
    system_info = {
        "OS": platform.system(),
        "Version": platform.version(),
        "Architecture": platform.architecture()[0],
        "CPU": cpuinfo.get_cpu_info()['brand_raw'],
        "Cores": psutil.cpu_count(logical=False),
        "Threads": psutil.cpu_count(logical=True),
        "RAM (Total)": f"{round(psutil.virtual_memory().total / (1024 ** 3), 2)} GB"
    }
    return system_info

def display_live_info(stdscr):
    """Display live system and GPU information using curses."""
    nvml = NVMLWrapper()

    while True:
        stdscr.clear()

        # Fetch system information
        system_info = get_system_info()
        stdscr.addstr(0, 0, "System Information:")
        stdscr.addstr(1, 0, tabulate(system_info.items(), headers=["Component", "Details"], tablefmt="grid"))

        # Display resource usage
        cpu_usage = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory()
        stdscr.addstr(3, 0, "\nResource Usage:")
        stdscr.addstr(4, 0, f"CPU Usage: {cpu_usage}%")
        stdscr.addstr(5, 0, f"RAM Usage: {ram.used / (1024 ** 3):.2f} GB / {ram.total / (1024 ** 3):.2f} GB")

        # Display GPU information
        gpus = nvml.list_gpus()
        total_power = 0
        for gpu in gpus:
            current_power = gpu['power_usage']
            if current_power is not None:
                total_power += current_power
            power_str = f"{current_power:.1f} W" if current_power is not None else "N/A"
            stdscr.addstr(6 + gpu['id'], 0, f"GPU {gpu['id']} Power: {power_str}")

        stdscr.addstr(6 + len(gpus), 0, f"Total GPU Power: {total_power:.1f} W")

        # Display user options
        stdscr.addstr(8 + len(gpus), 0, "\nPress 'c' to configure GPUs or 'q' to quit.")
        stdscr.refresh()

        # Handle user input
        key = stdscr.getch()
        if key == ord('q'):
            break
        elif key == ord('c'):
            configure_gpu(nvml)

def configure_gpu(nvml):
    """Allow user to configure GPU settings."""
    gpus = nvml.list_gpus()

    print("Available GPUs:")
    for gpu in gpus:
        print(f"{gpu['id'] + 1}. {gpu['name']} (Memory: {gpu['memory']} MB, Power Limit: {gpu['power_limit']} W)")

    choice = int(input("Select GPU to configure (number): ")) - 1
    if 0 <= choice < len(gpus):
        gpu = gpus[choice]
        handle = c_void_p()
        nvml.nvml_lib.nvmlDeviceGetHandleByIndex_v2(gpu['id'], byref(handle))

        # Set memory frequency
        mem_freq_input = input("Set memory frequency in MHz (press Enter to keep current): ").strip()
        if mem_freq_input:
            try:
                mem_freq = int(mem_freq_input)
                nvml.set_memory_frequency(handle, mem_freq)
                print(f"Memory Frequency updated to {mem_freq} MHz")
            except ValueError:
                print("Invalid memory frequency value. Keeping current setting.")

        # Set power limit
        power_limit_input = input("Set power limit in W (press Enter to keep current): ").strip()
        if power_limit_input:
            try:
                power_limit = int(power_limit_input)
                nvml.set_power_limit(handle, power_limit)
                print(f"Power limit updated to {power_limit} W")
            except ValueError:
                print("Invalid power limit value. Keeping current setting.")

        print(f"\nConfiguration complete for {gpu['name']}")
    else:
        print("Invalid selection.")

def main(stdscr):
    """Main function to display menu and handle user actions."""
    display_live_info(stdscr)

if __name__ == "__main__":
    curses.wrapper(main)
