import subprocess
import sys

# --- ANSI Color Codes for better output ---
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'

# This list must contain ALL packages from the debloat script to ensure a full restore.
PACKAGES_TO_REINSTALL = [
    "com.coloros.browser", "com.heytap.browser", "com.coloros.assistantscreen",
    "com.oppo.market", "com.heytap.market", "com.opos.cs", "com.realme.hotapps",
    "com.coloros.video", "com.heytap.music", "com.heytap.cloud",
    "com.facebook.system", "com.facebook.appmanager", "com.facebook.katana",
    "com.finshell.fin", "com.glance.internet", "com.realmestore.app",
    "com.realmecomm.app", "com.heytap.pictorial", "com.oppo.gamecenter",
    "com.coloros.gamespaceui", "com.coloros.phonemanager", "com.coloros.filemanager",
    "com.coloros.weather2", "com.coloros.soundrecorder", "com.heytap.themestore",
    "com.heytap.usercenter", "com.coloros.calculator", "com.coloros.alarmclock",

    # Xiaomi / Mi leftovers (matches debloat script)
    "com.mi.android.globalFileexplorer", "com.mi.global.shop", "com.miui.videoplayer",
    "com.mi.globalbrowser", "com.mi.global.bbs", "com.xiaomi.smarthome", "com.xiaomi.hm.health",
    "com.xiaomi.router",

    # Additional Realme / ColorOS components (advanced optional set)
    "com.oplus.themestore", "com.oplus.wallpapers", "com.coloros.childrenspace",
    "com.coloros.translate", "com.coloros.translate.engine", "com.oplus.weather.service",
    "com.oplus.safecenter", "com.oplus.screenrecorder", "com.oplus.statistics.rom",
    "com.oplus.smartengine", "com.oplus.operationManual", "com.oplus.beaconlink"
]

def check_adb_device():
    # (Same function as in the debloat script)
    try:
        result = subprocess.run(['adb', 'devices'], capture_output=True, text=True, check=True)
        output_lines = result.stdout.strip().split('\n')
        if len(output_lines) == 2 and output_lines[1].endswith('\tdevice'):
            device_id = output_lines[1].split('\t')[0]
            print(f"{Colors.GREEN}✔ Device {device_id} found and authorized.{Colors.END}\n")
            return True
        else:
            print(f"{Colors.RED}Error: No authorized ADB device found or multiple devices connected.{Colors.END}")
            return False
    except (FileNotFoundError, subprocess.CalledProcessError):
        print(f"{Colors.RED}Error: ADB is not working correctly.{Colors.END}")
        return False

def main():
    """Main function to run the reinstallation process."""
    print(f"{Colors.BOLD}--- Realme GT 6 Package Reinstaller ---{Colors.END}")

    if not check_adb_device():
        sys.exit(1)

    print(f"{Colors.YELLOW}This will attempt to restore {len(PACKAGES_TO_REINSTALL)} packages.{Colors.END}")
    try:
        confirm = input(f"Are you sure you want to continue? (y/n): {Colors.END}").lower()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)

    if confirm != 'y':
        print("Operation cancelled.")
        sys.exit(0)

    print("\nStarting reinstallation process...\n")
    success_count = 0
    fail_count = 0
    for package in sorted(PACKAGES_TO_REINSTALL):
        command = ['adb', 'shell', 'cmd', 'package', 'install-existing', package]
        result = subprocess.run(command, capture_output=True, text=True)
        
        if "Package " in result.stdout and " installed for user: 0" in result.stdout:
            print(f"  {Colors.GREEN}[✔] Successfully reinstalled {package}{Colors.END}")
            success_count += 1
        else:
            # This often means the package was never uninstalled, which is not an error.
            print(f"  {Colors.YELLOW}[!] Package likely already installed or not found: {package}{Colors.END}")
            fail_count += 1
            
    print(f"\n{Colors.BOLD}--- Reinstallation Complete ---{Colors.END}")
    print(f"{Colors.GREEN}Successfully reinstalled: {success_count} packages.{Colors.END}")
    print(f"{Colors.YELLOW}Already present or not found: {fail_count} packages.{Colors.END}")

if __name__ == "__main__":
    main()
