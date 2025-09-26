#!/usr/bin/env python3
"""
Multicast Route Validator (Cisco + Netgear)
-------------------------------------------
- Validates IGMP querier status, duplicate queriers, multicast floods.
- Interactive setup (no CLI flags needed).
- Pretty CLI reports (Rich).
- Bootstraps dependencies.
- Validates Python version and installs/updates Python + build tools on Linux & Windows.
"""

import site, sys

# Ensure user packages are visible
if site.getusersitepackages() not in sys.path:
    sys.path.append(site.getusersitepackages())

import os
import platform
import subprocess
import urllib.request
import time
import re
import getpass
import ipaddress
import socket

MIN_PYTHON = (3, 8)

# -------------------------------------------------
# Step 1: Check Python Version
# -------------------------------------------------
def check_python_version():
    current = sys.version_info
    if current < MIN_PYTHON:
        print(f" Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+ required, found {current.major}.{current.minor}")
        install_or_upgrade_python()
    else:
        print(f" Python version OK: {current.major}.{current.minor}")

# -------------------------------------------------
# Step 2: Install/Upgrade Python + Build Tools
# -------------------------------------------------
def install_or_upgrade_python():
    os_type = platform.system().lower()

    if os_type == "linux":
        install_python_linux()
    elif os_type == "windows":
        install_python_windows()
    elif os_type == "darwin":  # MacOS
        print(" Auto-install for MacOS not supported. Please run:\n"
              "brew install python3\n"
              "or download installer from https://www.python.org/downloads/macos/")
        sys.exit(1)
    else:
        print(" Unsupported OS for auto-install.")
        sys.exit(1)

def install_python_linux():
    try:
        with open("/etc/os-release") as f:
            release = f.read().lower()

        if "ubuntu" in release or "debian" in release:
            subprocess.check_call(["sudo", "apt-get", "update"])
            subprocess.check_call(["sudo", "apt-get", "install", "-y",
                                   "python3.9", "python3.9-distutils", "python3-pip",
                                   "build-essential", "rustc", "cargo"])
        elif any(distro in release for distro in ["rhel", "centos", "rocky", "almalinux"]):
            subprocess.check_call(["sudo", "yum", "install", "-y",
                                   "python39", "python39-pip",
                                   "gcc", "gcc-c++", "make", "rust", "cargo"])
        else:
            print(" Unsupported Linux distribution. Install Python manually.")
            sys.exit(1)

        print(" Python + build tools installed/upgraded successfully.")

        # Relaunch with new Python
        new_python = "/usr/bin/python3.9" if os.path.exists("/usr/bin/python3.9") else "python3.9"
        print(f" Restarting script with {new_python}...")
        os.execvp(new_python, [new_python] + sys.argv)

    except Exception as e:
        print(f" Failed to install Python/build tools: {e}")
        sys.exit(1)

def install_python_windows():
    try:
        url = "https://www.python.org/ftp/python/3.12.5/python-3.12.5-amd64.exe"
        installer = "python-installer.exe"
        print("Downloading Python installer for Windows...")
        urllib.request.urlretrieve(url, installer)

        print("Running installer...")
        subprocess.check_call([installer, "/quiet", "InstallAllUsers=1", "PrependPath=1", "Include_pip=1"])

        print(" Python installed successfully. Restart your terminal if needed.")
        sys.exit(0)
    except Exception as e:
        print(f" Failed to install Python on Windows: {e}")
        sys.exit(1)

# Run version check early
check_python_version()

# -------------------------------------------------
# Step 3: Dependency Installer
# -------------------------------------------------
REQUIRED_PACKAGES = ["netmiko", "pysnmp", "rich"]

def install_dependencies():
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade",
                               "pip", "setuptools", "wheel", "setuptools-rust", "--user"])
    except Exception as e:
        print(f" Warning: could not upgrade pip/setuptools properly: {e}")

    for pkg in REQUIRED_PACKAGES:
        try:
            __import__(pkg)
        except ImportError:
            print(f"[INFO] Installing missing dependency: {pkg}")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", pkg])
            except subprocess.CalledProcessError as e:
                print(f" Failed to install {pkg}. Error: {e}")
                sys.exit(1)

install_dependencies()

# -------------------------------------------------
# Step 4: Imports after ensuring installation
# -------------------------------------------------
from netmiko import ConnectHandler
from rich.console import Console
from rich.table import Table
from rich import box

console = Console()

# -------------------------------------------------
# Switch Handler Base Class
# -------------------------------------------------
class SwitchHandler:
    def __init__(self, hostname: str, username: str, password: str, device_type: str, port: int = 22):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.device_type = device_type
        self.port = port
        self.connection = None

    def connect(self):
        try:
            self.connection = ConnectHandler(
                device_type=self.device_type,
                host=self.hostname,
                username=self.username,
                password=self.password,
                port=self.port
            )
            console.print(f" Connected to {self.hostname}:{self.port} ({self.device_type})")
        except Exception as e:
            console.print(f" Connection failed to {self.hostname}:{self.port}: {e}")
            sys.exit(1)

    def disconnect(self):
        try:
            if self.connection:
                self.connection.disconnect()
                console.print(f" Disconnected from {self.hostname}")
        except Exception as e:
            console.print(f"Error disconnecting: {e}")

    def get_multicast_info(self):
        raise NotImplementedError("Must implement in subclass")

# -------------------------------------------------
# Cisco Handler
# -------------------------------------------------
class CiscoHandler(SwitchHandler):
    def get_multicast_info(self):
        output = {}
        try:
            output["igmp_groups"] = self.connection.send_command("show ip igmp groups")
            output["querier"] = self.connection.send_command("show ip igmp snooping querier")
            output["mroutes"] = self.connection.send_command("show ip mroute")
        except Exception as e:
            console.print(f"Error pulling Cisco data: {e}")
        return output

# -------------------------------------------------
# Netgear Handler
# -------------------------------------------------
class NetgearHandler(SwitchHandler):
    def get_multicast_info(self):
        output = {}
        try:
            output["igmp_groups"] = self.connection.send_command("show igmp group")
            output["querier"] = self.connection.send_command("show igmp querier")
            output["mroutes"] = self.connection.send_command("show ip mroute")
        except Exception as e:
            console.print(f"Error pulling Netgear data: {e}")
        return output

# -------------------------------------------------
# Multicast Validator
# -------------------------------------------------
class MulticastValidator:
    def __init__(self, handler: SwitchHandler):
        self.handler = handler

    def run_validation(self):
        try:
            data = self.handler.get_multicast_info()

            table = Table(title=f"Multicast Validation Report - {self.handler.hostname}", box=box.MINIMAL_DOUBLE_HEAD)
            table.add_column("Check", style="cyan", justify="left")
            table.add_column("Result", style="magenta", justify="left")

            # Querier validation
            if not data.get("querier"):
                table.add_row("Querier", "No querier data")
            elif "no querier" in data["querier"].lower():
                table.add_row("Querier", "No active IGMP querier")
            elif "multiple" in data["querier"].lower():
                table.add_row("Querier", "Multiple queriers detected")
            else:
                table.add_row("Querier", "OK")

            # Flood detection heuristic
            if "mroutes" in data and "(*,G)" in data["mroutes"]:
                table.add_row("Flood Detection", "Flooded groups detected")
            else:
                table.add_row("Flood Detection", "No flood")

            # IGMP group membership
            if not data.get("igmp_groups"):
                table.add_row("IGMP Groups", "No groups detected")
            else:
                table.add_row("IGMP Groups", "Groups retrieved")

            console.print(table)
            return data
        except Exception as e:
            console.print(f" Validation failed: {e}")
            return {}

# -------------------------------------------------
# Monitoring Loop
# -------------------------------------------------
def monitor_loop(handler: SwitchHandler, interval: int = 60):
    validator = MulticastValidator(handler)
    try:
        while True:
            console.print(f"\n Running multicast validation for {handler.hostname}...")
            validator.run_validation()
            time.sleep(interval)
    except KeyboardInterrupt:
        console.print(" Monitoring stopped by user.")
    except Exception as e:
        console.print(f" Error in monitoring loop: {e}")

# -------------------------------------------------
# Interactive Input with Validation + Reachability
# -------------------------------------------------
def validate_ip_or_hostname(value: str) -> bool:
    try:
        # Strict IP validation
        ipaddress.ip_address(value)
        return True
    except ValueError:
        # Fallback to hostname validation
        hostname_pattern = r"^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))*$"
        return bool(re.match(hostname_pattern, value))

def validate_nonempty(value: str) -> bool:
    return bool(value.strip())

def validate_vendor(value: str) -> bool:
    return value.lower() in ["cisco", "netgear"]

def validate_interval(value: str) -> bool:
    return value.isdigit() and int(value) >= 0

def is_reachable(host: str, port: int) -> bool:
    """Check if host is reachable via ping or TCP on the given port."""
    try:
        # Try ICMP ping
        ping_cmd = ["ping", "-c", "1", "-W", "1", host] if platform.system().lower() != "windows" else ["ping", "-n", "1", host]
        if subprocess.call(ping_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
            return True
    except Exception:
        pass

    # Fallback: TCP check
    try:
        with socket.create_connection((host, port), timeout=2):
            return True
    except Exception:
        return False

def get_user_inputs():
    try:
        console.print("\n[bold cyan]=== Multicast Route Validator Setup ===[/bold cyan]")

        # Hostname/IP
        while True:
            hostname = input("Enter switch hostname/IP: ").strip()
            if validate_ip_or_hostname(hostname):
                break
            console.print(" Invalid hostname or IP. Please try again.")

        # SSH Port
        while True:
            port_input = input("Enter SSH port (default 22): ").strip()
            port = 22 if port_input == "" else int(port_input) if port_input.isdigit() else -1
            if port > 0 and is_reachable(hostname, port):
                break
            console.print(" Invalid or unreachable port. Please try again.")

        # Username
        while True:
            username = input("Enter SSH username: ").strip()
            if validate_nonempty(username):
                break
            console.print(" Username cannot be empty. Please try again.")

        # Password (hidden input)
        while True:
            password = getpass.getpass("Enter SSH password: ").strip()
            if validate_nonempty(password):
                break
            console.print(" Password cannot be empty. Please try again.")

        # Vendor
        while True:
            vendor = input("Enter vendor (cisco/netgear): ").strip().lower()
            if validate_vendor(vendor):
                break
            console.print(" Vendor must be either 'cisco' or 'netgear'.")

        # Interval
        while True:
            interval = input("Polling interval in seconds (0 = run once): ").strip()
            if validate_interval(interval):
                interval = int(interval)
                break
            console.print(" Interval must be a number >= 0.")

        if vendor == "cisco":
            handler = CiscoHandler(hostname, username, password, "cisco_ios", port)
        else:
            handler = NetgearHandler(hostname, username, password, "netgear_prosafe", port)

        return handler, interval

    except Exception as e:
        console.print(f" Error collecting inputs: {e}")
        sys.exit(1)

# -------------------------------------------------
# Main
# -------------------------------------------------
def main():
    handler, interval = get_user_inputs()
    handler.connect()

    try:
        if interval > 0:
            monitor_loop(handler, interval)
        else:
            validator = MulticastValidator(handler)
            validator.run_validation()
    except Exception as e:
        console.print(f" Runtime error: {e}")
    finally:
        handler.disconnect()

if __name__ == "__main__":
    main()
