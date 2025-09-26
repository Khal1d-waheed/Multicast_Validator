# Multicast Route Validator

A cross-platform **diagnostic and monitoring tool** for validating multicast health on **AV networks** (Dante, Q-SYS, Crestron NVX, etc.).  
Supports **Cisco** and **Netgear AV switches** out of the box.  

It automatically verifies **IGMP queriers, multicast memberships, pruning, and routing** to prevent common AV network issues such as **audio dropouts, video freezes, and network flooding**.  

---

## Features

-  **Vendor Support**: Works with **Cisco IOS/IOS-XE** and **Netgear ProSAFE/AV Line** switches.  
-  **Protocol Awareness**:  
  - Validates **IGMP snooping** & **querier election**.  
  - Checks multicast routing tables (`mroutes`).  
  - Detects **flooded groups** (pruning issues).  
-  **Cross-Platform Bootstrap**:  
  - Validates Python installation (`>=3.8`).  
  - Auto-installs/updates Python on **Linux (Ubuntu/RHEL)** and **Windows**.  
  - Guides for macOS users.  
-  **Self-Bootstrapping**: Installs all dependencies (`netmiko`, `pysnmp`, `rich`) automatically.  
-  **Interactive CLI**: Step-by-step prompts for host, credentials, vendor, and monitoring interval.  
-  **Rich Reports**: Beautiful, color-coded CLI tables (Querier, Flood Detection, IGMP Groups).  
-  **Real-Time Monitoring**: Runs periodically at user-defined intervals.  
-  **Resilient**: Full exception handling; script never crashes unexpectedly.  

---

##  Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/Khal1d-waheed/Multicast_Validator.git
cd multicast-validator
```
### 2. Run the Validator
```
python3 multicast_validator.py
```
If Python or dependencies are missing, the script will automatically:
- Install/upgrade Python (Linux/Windows).
- Install required Python packages (netmiko, pysnmp, rich).

---
### Running the Script

You can run the Multicast Route Validator on both **Windows** and **Linux**.

###  Windows
1. Open **Command Prompt** or **PowerShell**.
2. Navigate to the project directory:
``` powershell
   cd C:\path\to\multicast-validator
```
3. Run the Script
```
 python multicast_validator.py
```

### Linux(Ubuntu, RHEL, CentOS, Rocky, Alma)
1. Open a Terminal
2. Navigate to the project directory
```
cd ~/multicast-route-validator
``` 
3. Run the Script:
```
python3 multicast_validator.py
```

## Interactive Setup
When the script is run it prompts you for the following:
```
=== Multicast Route Validator Setup ===
Enter switch hostname/IP: 192.168.1.10
Enter SSH username: admin
Enter SSH password: *****
Enter vendor (cisco/netgear): cisco
Polling interval in seconds (0 = run once): 60
```

## Supported Commands

The tool automatically runs vendor-appropriate commands:

**Cisco IOS/IOS-XE**
- `show ip igmp groups`
- `show ip igmp snooping querier`
- `show ip mroute`

**Netgear ProSAFE / AV Line**
- `show igmp group`
- `show igmp querier`
- `show ip mroute` (if supported)

---

## Dependencies

- [Python 3.8+](https://www.python.org/downloads/)  
- [netmiko](https://pypi.org/project/netmiko/) – SSH automation for network devices.  
- [pysnmp](https://pypi.org/project/pysnmp/) – SNMP support (future expansion).  
- [rich](https://pypi.org/project/rich/) – Pretty CLI tables & color output.  

The script installs all dependencies automatically at runtime.  

---

## Limitations

- Requires **SSH access** to switches.  
- Needs **sudo/admin rights** for automatic Python installation on Linux/Windows.  
- **MacOS auto-install not supported** (manual steps provided).  
- Currently supports **Cisco IOS/IOS-XE** and **Netgear AV switches**.  
