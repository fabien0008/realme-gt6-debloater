import subprocess
import sys

# --- ANSI Color Codes for better output ---
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'

# --- List of packages to uninstall based on your choices ---
# Category 1: Safe to Remove Bloatware
SAFE_PACKAGES = [
    "com.coloros.browser",          # Default Browser
    "com.heytap.browser",           # Default Browser
    "com.coloros.assistantscreen",  # Realme's version of Google Discover
    "com.oppo.market",              # App Market
    "com.heytap.market",            # App Market
    "com.opos.cs",                  # App Recommendations (Hot Apps/Games)
    "com.realme.hotapps",           # App Recommendations (Hot Apps/Games)
    "com.coloros.video",            # Default Video Player
    "com.heytap.music",             # Default Music Player
    "com.heytap.cloud",             # Realme's Cloud Service
    "com.facebook.system",          # Facebook Services
    "com.facebook.appmanager",      # Facebook App Manager
    "com.facebook.katana",          # Facebook App
    "com.finshell.fin",             # Payment Service (non-EU)
    "com.glance.internet",          # Lockscreen Content Service
    "com.realmestore.app",          # Realme Store App
    "com.realmecomm.app",           # Realme Community App
    "com.heytap.pictorial"          # Lockscreen Magazine
]

# Category 2: Advanced User Choices (You confirmed you want these removed)
ADVANCED_PACKAGES = [
    "com.oppo.gamecenter",          # Game Center (You are not a gamer)
    "com.coloros.gamespaceui",      # Game Space UI (You are not a gamer)
    "com.coloros.phonemanager",     # Phone Manager / Optimizer
    "com.coloros.filemanager",      # Default File Manager
    "com.coloros.weather2",         # Default Weather Service
    "com.coloros.soundrecorder",    # Default Sound Recorder
    "com.heytap.themestore",        # Official Theme Store
    "com.heytap.usercenter",        # HeyTap Account Center
    "com.coloros.calculator",       # Default Calculator
    "com.coloros.alarmclock"        # Default Clock/Alarm app. Ensure you have Google Clock or other alternative.
]

# Master list of all packages to be uninstalled
PACKAGES_TO_UNINSTALL = sorted(SAFE_PACKAGES + ADVANCED_PACKAGES)

def check_adb_device():
    """Checks for a single, authorized ADB device."""
    try:
        result = subprocess.run(['adb', 'devices'], capture_output=True, text=True, check=True)
        output_lines = result.stdout.strip().split('\n')
        # Expecting ['List of devices attached', '1641310c\tdevice']
        if len(output_lines) == 2 and output_lines[1].endswith('\tdevice'):
            device_id = output_lines[1].split('\t')[0]
            print(f"{Colors.GREEN}✔ Device {device_id} found and authorized.{Colors.END}\n")
            return True
        else:
            print(f"{Colors.RED}Error: No authorized ADB device found or multiple devices connected.")
            print("Please ensure one phone is connected and USB Debugging is enabled and authorized.{Colors.END}")
            return False
    except FileNotFoundError:
        print(f"{Colors.RED}Error: 'adb' command not found. Is ADB Platform Tools installed and in your PATH?{Colors.END}")
        return False
    except subprocess.CalledProcessError:
        print(f"{Colors.RED}Error: 'adb devices' command failed.{Colors.END}")
        return False

def main():
    """Main function to run the debloating process."""
    print(f"{Colors.BOLD}--- Realme GT 6 Python Debloater ---{Colors.END}")
    
    if not check_adb_device():
        sys.exit(1)

    print(f"{Colors.YELLOW}This script will attempt to uninstall the following {len(PACKAGES_TO_UNINSTALL)} packages:{Colors.END}")
    for pkg in PACKAGES_TO_UNINSTALL:
        print(f"  - {pkg}")
    
    print(f"\n{Colors.BOLD}{Colors.YELLOW}This action is non-destructive and can be reversed by a factory reset or the reinstall script.")
    
    try:
        confirm = input(f"Are you sure you want to continue? (y/n): {Colors.END}").lower()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)

    if confirm != 'y':
        print("Operation cancelled.")
        sys.exit(0)

    print("\nStarting uninstallation process...\n")
    success_count = 0
    fail_count = 0
    for package in PACKAGES_TO_UNINSTALL:
        command = ['adb', 'shell', 'pm', 'uninstall', '-k', '--user', '0', package]
        result = subprocess.run(command, capture_output=True, text=True)
        
        if "Success" in result.stdout:
            print(f"  {Colors.GREEN}[✔] Successfully uninstalled {package}{Colors.END}")
            success_count += 1
        else:
            # This often means the package was not installed in the first place, which is fine.
            print(f"  {Colors.YELLOW}[!] Failed or package not found: {package}{Colors.END}")
            fail_count += 1
            
    print(f"\n{Colors.BOLD}--- Debloating Complete ---{Colors.END}")
    print(f"{Colors.GREEN}Successfully uninstalled: {success_count} packages.{Colors.END}")
    print(f"{Colors.YELLOW}Failed or not found: {fail_count} packages.{Colors.END}")

if __name__ == "__main__":
    main()
