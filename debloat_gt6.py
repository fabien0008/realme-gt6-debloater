# Standard library imports
import argparse
import subprocess
import sys
from datetime import datetime

# --- ANSI Color Codes for better output ---
# ---------------------------------------------------------------------------
# UI helpers (ANSI colors)
# ---------------------------------------------------------------------------

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

    # --- Xiaomi / Mi leftovers that can safely be removed ---
    "com.mi.android.globalFileexplorer", # Mi File Manager
    "com.mi.global.shop",               # Mi Store
    "com.miui.videoplayer",             # Mi Video
    "com.mi.globalbrowser",             # Mi Browser
    "com.mi.global.bbs",                # Mi Community
    "com.xiaomi.smarthome",             # Xiaomi Home / Mi Home
    "com.xiaomi.hm.health",             # Mi Fitness
    "com.xiaomi.router"                 # Mi Wi-Fi / Mi Router
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

    # --- Additional Realme / ColorOS components (non-critical) ---
    "com.oplus.themestore",         # Updated Theme Store package name
    "com.oplus.wallpapers",         # Stock & online wallpapers
    "com.coloros.childrenspace",    # Kids mode
    "com.coloros.translate",        # Realme Translate front-end
    "com.coloros.translate.engine", # Realme Translate engine
    "com.oplus.weather.service",    # Weather backend
    "com.oplus.safecenter",         # Optimizer / Phone Manager
    "com.oplus.screenrecorder",     # Built-in screen recorder
    "com.oplus.statistics.rom",     # Telemetry service
    "com.oplus.smartengine",        # Smart Engine (analytics)
    "com.oplus.operationManual",    # Interactive user manual
    "com.oplus.beaconlink"          # Device-to-device discovery
]

# Master list of all packages to be uninstalled
# By default we uninstall both safe and advanced packages ("full" profile).
# In minimal profile we keep only the unquestionably safe bloatware set.
FULL_PACKAGES = sorted(SAFE_PACKAGES + ADVANCED_PACKAGES)

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _run(cmd):
    """Run a subprocess command and return CompletedProcess (convenience wrapper)."""
    return subprocess.run(cmd, capture_output=True, text=True)


def check_adb_device():
    """Checks for a single, authorized ADB device and returns its serial if OK."""
    try:
        result = subprocess.run(['adb', 'devices'], capture_output=True, text=True, check=True)
    except FileNotFoundError:
        print(f"{Colors.RED}Error: 'adb' command not found in PATH. Install platform-tools first.{Colors.END}")
        return None
    except subprocess.CalledProcessError:
        print(f"{Colors.RED}Error: 'adb devices' failed. Is adb server running?{Colors.END}")
        return None

    lines = [l for l in result.stdout.strip().split('\n') if l.strip()]
    # Remove header line if present
    lines = [l for l in lines if not l.lower().startswith('list of devices')]

    if len(lines) != 1 or not lines[0].endswith('\tdevice'):
        print(f"{Colors.RED}Error: Exactly one authorized device required but {len(lines)} found.{Colors.END}")
        return None

    serial = lines[0].split('\t')[0]
    print(f"{Colors.GREEN}✔ Device {serial} found and authorized.{Colors.END}\n")
    return serial


def fetch_device_props(serial):
    """Return dict with selected build properties for logging purposes."""
    props_of_interest = {
        'ro.product.model': 'Model',
        'ro.build.version.release': 'Android',
        'ro.build.version.oplusrom': 'RealmeUI',
        'ro.build.fingerprint': 'Fingerprint',
    }
    props = {}
    for key in props_of_interest:
        cp = _run(['adb', '-s', serial, 'shell', 'getprop', key])
        if cp.returncode == 0:
            props[props_of_interest[key]] = cp.stdout.strip()
    return props


def get_installed_packages(serial):
    """Return a set of package names currently installed for user 0 on the device."""
    cp = _run(['adb', '-s', serial, 'shell', 'pm', 'list', 'packages', '--user', '0'])
    if cp.returncode != 0:
        return set()
    # lines look like: package:com.foo.bar
    pkgs = {line.split(':', 1)[1].strip() for line in cp.stdout.splitlines() if line.startswith('package:')}
    return pkgs

def parse_args():
    parser = argparse.ArgumentParser(description="Debloat Realme GT 6 using adb pm uninstall --user 0")
    parser.add_argument('-m', '--minimal', action='store_true', help='Remove only the unquestionably safe bloatware set ( keep default utilities ).')
    parser.add_argument('-n', '--dry-run', action='store_true', help='Do not execute adb uninstall, just print what would be done.')
    parser.add_argument('-l', '--log', action='store_true', help='Write a timestamped log file with all operations.')
    return parser.parse_args()


def log_line(fp, text):
    if fp:
        fp.write(text + '\n')


def main():
    args = parse_args()

    print(f"{Colors.BOLD}--- Realme GT 6 Debloater ---{Colors.END}")

    serial = check_adb_device()
    if not serial:
        sys.exit(1)

    # Determine package list
    wanted_packages = SAFE_PACKAGES if args.minimal else FULL_PACKAGES

    print(f"{Colors.YELLOW}Selected profile: {'minimal' if args.minimal else 'full'} ({len(wanted_packages)} packages).{Colors.END}\n")

    device_props = fetch_device_props(serial)
    if device_props:
        print("Device information:")
        for k, v in device_props.items():
            print(f"  {k}: {v}")
        print()

    installed_pkgs = get_installed_packages(serial)

    # Filter only those really present – allows safe re-runs without noise
    packages = [p for p in wanted_packages if p in installed_pkgs]
    skipped_packages = [p for p in wanted_packages if p not in installed_pkgs]

    if not packages:
        print(f"{Colors.GREEN}All target packages already absent – nothing to do.\n{Colors.END}")
        sys.exit(0)

    print("Packages that will be uninstalled (present on device):")
    for pkg in packages:
        print(f"  - {pkg}")

    if skipped_packages:
        print(f"\n{Colors.YELLOW}The following {len(skipped_packages)} packages are already missing (will be skipped):{Colors.END}")
        for pkg in skipped_packages:
            print(f"  - {pkg}")

    print(f"\n{Colors.BOLD}{Colors.YELLOW}This action is non-destructive and can be reversed with factory reset or reinstall script.{Colors.END}")

    try:
        confirm = input("Proceed? (y/n): ").strip().lower()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)

    if confirm != 'y':
        print("Operation cancelled.")
        sys.exit(0)

    log_fp = None
    if args.log:
        ts = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        log_fp = open(f'debloat_{ts}.log', 'w', encoding='utf-8')
        log_line(log_fp, f"Profile: {'minimal' if args.minimal else 'full'}")
        log_line(log_fp, f"Device: {serial}")
        for k, v in device_props.items():
            log_line(log_fp, f"{k}: {v}")
        log_line(log_fp, '')

    print("\nStarting uninstallation...\n")
    success_count = 0
    fail_count = 0

    for package in packages:
        if args.dry_run:
            print(f"  {Colors.YELLOW}[DRY-RUN] Would uninstall {package}{Colors.END}")
            log_line(log_fp, f"SKIP (dry-run): {package}")
            continue

        cp = _run(['adb', '-s', serial, 'shell', 'pm', 'uninstall', '-k', '--user', '0', package])

        if 'Success' in cp.stdout:
            print(f"  {Colors.GREEN}[✔] {package}{Colors.END}")
            log_line(log_fp, f"OK: {package}")
            success_count += 1
        else:
            print(f"  {Colors.YELLOW}[!] Failed or not present: {package}{Colors.END}")
            log_line(log_fp, f"FAIL: {package} | {cp.stdout.strip()} {cp.stderr.strip()}")
            fail_count += 1

    log_line(log_fp, f"Summary -> success {success_count}, fail {fail_count}")
    if log_fp:
        log_fp.close()

    print(f"\n{Colors.BOLD}--- Finished ---{Colors.END}")
    print(f"{Colors.GREEN}Successfully uninstalled: {success_count}{Colors.END}")
    print(f"{Colors.YELLOW}Failed/not found: {fail_count}{Colors.END}")


if __name__ == '__main__':
    main()
