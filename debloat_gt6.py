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

# --- Feature-based package categories ---
FEATURE_CATEGORIES = {
    "ai_features": {
        "name": "AI Features",
        "description": "AI Screen Recognition, Smart Assistant, AI Unit, and related AI functionality",
        "packages": [
            "com.coloros.assistantscreen",      # AI Screen Recognition / Smart Assistant
            "com.oplus.aiunit",                 # AI Unit - Core AI functionality
            "com.coloros.accessibilityassistant", # Accessibility Assistant
            "com.coloros.floatassistant",       # Float Assistant
            "com.coloros.smartsidebar",         # Smart Sidebar
            "com.coloros.lockassistant",        # Lock Screen Assistant
            "com.oplus.android.overlay.aifunction.cicletosearch", # AI Circle to Search overlay
            "com.oplus.android.overlay.aifunction.common",        # AI Common functions overlay
            "com.aiunit.aon",                   # AI Unit Always-On functionality
        ]
    },
    "browsers": {
        "name": "Default Browsers", 
        "description": "ColorOS and HeyTap default browsers",
        "packages": [
            "com.coloros.browser",          # Default Browser
            "com.heytap.browser",           # Default Browser
        ]
    },
    "app_stores": {
        "name": "App Stores & Markets",
        "description": "Alternative app markets and recommendations",
        "packages": [
            "com.oppo.market",              # App Market
            "com.heytap.market",            # App Market
            "com.opos.cs",                  # App Recommendations (Hot Apps/Games)
            "com.realme.hotapps",           # App Recommendations (Hot Apps/Games)
            "com.realmestore.app",          # Realme Store App
        ]
    },
    "media_apps": {
        "name": "Media Apps",
        "description": "Default video, music, and media applications",
        "packages": [
            "com.coloros.video",            # Default Video Player
            "com.heytap.music",             # Default Music Player
            "com.coloros.soundrecorder",    # Default Sound Recorder
        ]
    },
    "cloud_services": {
        "name": "Cloud & Online Services",
        "description": "Cloud storage, lockscreen content, community apps",
        "packages": [
            "com.heytap.cloud",             # Realme's Cloud Service
            "com.glance.internet",          # Lockscreen Content Service
            "com.realmecomm.app",           # Realme Community App
            "com.heytap.pictorial",         # Lockscreen Magazine
            "com.heytap.usercenter",        # HeyTap Account Center
        ]
    },
    "facebook": {
        "name": "Facebook Services",
        "description": "Facebook system services and apps",
        "packages": [
            "com.facebook.system",          # Facebook Services
            "com.facebook.appmanager",      # Facebook App Manager
            "com.facebook.katana",          # Facebook App
        ]
    },
    "gaming": {
        "name": "Gaming Features",
        "description": "Game center, game space, and gaming-related features",
        "packages": [
            "com.oppo.gamecenter",          # Game Center
            "com.coloros.gamespaceui",      # Game Space UI
        ]
    },
    "system_utilities": {
        "name": "System Utilities",
        "description": "File manager, phone manager, calculator, clock",
        "packages": [
            "com.coloros.phonemanager",     # Phone Manager / Optimizer
            "com.coloros.filemanager",      # Default File Manager
            "com.coloros.calculator",       # Default Calculator
            "com.coloros.alarmclock",       # Default Clock/Alarm app
        ]
    },
    "theming": {
        "name": "Themes & Wallpapers",
        "description": "Theme stores, wallpapers, and customization",
        "packages": [
            "com.heytap.themestore",        # Official Theme Store
            "com.oplus.themestore",         # Updated Theme Store package name
            "com.oplus.wallpapers",         # Stock & online wallpapers
        ]
    },
    "weather": {
        "name": "Weather Services",
        "description": "Weather apps and backend services",
        "packages": [
            "com.coloros.weather2",         # Default Weather Service
            "com.oplus.weather.service",    # Weather backend
        ]
    },
    "translation": {
        "name": "Translation Services",
        "description": "Realme translate functionality",
        "packages": [
            "com.coloros.translate",        # Realme Translate front-end
            "com.coloros.translate.engine", # Realme Translate engine
        ]
    },
    "kids_mode": {
        "name": "Kids Mode",
        "description": "Children's space and parental controls",
        "packages": [
            "com.coloros.childrenspace",    # Kids mode
        ]
    },
    "screen_recording": {
        "name": "Screen Recording",
        "description": "Built-in screen recorder",
        "packages": [
            "com.oplus.screenrecorder",     # Built-in screen recorder
        ]
    },
    "analytics": {
        "name": "Analytics & Telemetry",
        "description": "Data collection and analytics services",
        "packages": [
            "com.oplus.statistics.rom",     # Telemetry service
            "com.oplus.smartengine",        # Smart Engine (analytics)
        ]
    },
    "misc_features": {
        "name": "Miscellaneous Features",
        "description": "Other optional features and services",
        "packages": [
            "com.finshell.fin",             # Payment Service (non-EU)
            "com.oplus.operationManual",    # Interactive user manual
            "com.oplus.beaconlink",         # Device-to-device discovery
        ]
    },
    "xiaomi_leftovers": {
        "name": "Xiaomi/Mi Leftovers",
        "description": "Legacy Xiaomi/Mi packages that may be present",
        "packages": [
            "com.mi.android.globalFileexplorer", # Mi File Manager
            "com.mi.global.shop",               # Mi Store
            "com.miui.videoplayer",             # Mi Video
            "com.mi.globalbrowser",             # Mi Browser
            "com.mi.global.bbs",                # Mi Community
            "com.xiaomi.smarthome",             # Xiaomi Home / Mi Home
            "com.xiaomi.hm.health",             # Mi Fitness
            "com.xiaomi.router",                # Mi Wi-Fi / Mi Router
        ]
    }
}

# Legacy compatibility - maintain original package lists
SAFE_PACKAGES = []
ADVANCED_PACKAGES = []
for category_data in FEATURE_CATEGORIES.values():
    if category_data["name"] in ["AI Features", "Default Browsers", "App Stores & Markets", "Media Apps", 
                                 "Cloud & Online Services", "Facebook Services", "Xiaomi/Mi Leftovers"]:
        SAFE_PACKAGES.extend(category_data["packages"])
    else:
        ADVANCED_PACKAGES.extend(category_data["packages"])

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
    parser = argparse.ArgumentParser(description="Debloat/Restore Realme GT 6 packages using adb")
    
    # Operation mode
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument('--debloat', action='store_true', help='Remove packages (debloat mode)')
    mode_group.add_argument('--restore', action='store_true', help='Restore packages (reinstall mode)')
    mode_group.add_argument('--list-features', action='store_true', help='List all available feature categories')
    
    # Debloat options
    parser.add_argument('-m', '--minimal', action='store_true', help='Remove only the unquestionably safe bloatware set (debloat mode only)')
    
    # Selective operations
    parser.add_argument('--features', nargs='+', help='Specify feature categories to operate on (use --list-features to see available options)')
    parser.add_argument('--exclude-features', nargs='+', help='Exclude specific feature categories from operation')
    
    # General options
    parser.add_argument('-n', '--dry-run', action='store_true', help='Do not execute commands, just print what would be done')
    parser.add_argument('-l', '--log', action='store_true', help='Write a timestamped log file with all operations')
    parser.add_argument('-y', '--yes', action='store_true', help='Skip confirmation prompts (auto-confirm)')
    
    return parser.parse_args()


def log_line(fp, text):
    if fp:
        fp.write(text + '\n')


def list_feature_categories():
    """Display all available feature categories"""
    print(f"{Colors.BOLD}Available Feature Categories:{Colors.END}\n")
    for category_id, category_data in FEATURE_CATEGORIES.items():
        print(f"{Colors.BOLD}{category_id}{Colors.END}: {category_data['name']}")
        print(f"  Description: {category_data['description']}")
        print(f"  Packages ({len(category_data['packages'])}): {', '.join(category_data['packages'][:3])}{'...' if len(category_data['packages']) > 3 else ''}")
        print()


def get_packages_by_features(feature_list=None, exclude_features=None):
    """Get packages based on selected features"""
    if feature_list:
        # Only include specified features
        packages = []
        for feature in feature_list:
            if feature in FEATURE_CATEGORIES:
                packages.extend(FEATURE_CATEGORIES[feature]["packages"])
            else:
                print(f"{Colors.YELLOW}Warning: Unknown feature '{feature}' ignored{Colors.END}")
    else:
        # Include all packages
        packages = FULL_PACKAGES.copy()
    
    # Exclude specified features
    if exclude_features:
        for feature in exclude_features:
            if feature in FEATURE_CATEGORIES:
                for pkg in FEATURE_CATEGORIES[feature]["packages"]:
                    if pkg in packages:
                        packages.remove(pkg)
            else:
                print(f"{Colors.YELLOW}Warning: Unknown exclude feature '{feature}' ignored{Colors.END}")
    
    return sorted(set(packages))


def restore_packages(serial, packages, dry_run=False, log_fp=None):
    """Restore (reinstall) packages on the device"""
    print(f"\n{Colors.BOLD}Starting package restoration...{Colors.END}\n")
    success_count = 0
    fail_count = 0

    for package in packages:
        if dry_run:
            print(f"  {Colors.YELLOW}[DRY-RUN] Would restore {package}{Colors.END}")
            log_line(log_fp, f"SKIP (dry-run restore): {package}")
            continue

        cp = _run(['adb', '-s', serial, 'shell', 'cmd', 'package', 'install-existing', package])

        if "Package " in cp.stdout and " installed for user: 0" in cp.stdout:
            print(f"  {Colors.GREEN}[✔] Successfully restored {package}{Colors.END}")
            log_line(log_fp, f"RESTORE OK: {package}")
            success_count += 1
        else:
            print(f"  {Colors.YELLOW}[!] Already present or not found: {package}{Colors.END}")
            log_line(log_fp, f"RESTORE SKIP: {package} | {cp.stdout.strip()} {cp.stderr.strip()}")
            fail_count += 1

    log_line(log_fp, f"Restore Summary -> success {success_count}, skip/fail {fail_count}")
    return success_count, fail_count


def main():
    args = parse_args()

    # Handle list-features mode
    if args.list_features:
        list_feature_categories()
        return

    # Determine operation mode
    mode = "debloat" if args.debloat else "restore"
    print(f"{Colors.BOLD}--- Realme GT 6 {mode.title()} Tool ---{Colors.END}")

    serial = check_adb_device()
    if not serial:
        sys.exit(1)

    # Determine package list based on mode and options
    if args.features:
        # Use specific features
        wanted_packages = get_packages_by_features(args.features, args.exclude_features)
        profile_desc = f"custom features: {', '.join(args.features)}"
    elif args.minimal and mode == "debloat":
        # Minimal debloat
        wanted_packages = get_packages_by_features(exclude_features=args.exclude_features)
        wanted_packages = [p for p in wanted_packages if p in SAFE_PACKAGES]
        profile_desc = "minimal (safe packages only)"
    else:
        # Full mode (default)
        wanted_packages = get_packages_by_features(exclude_features=args.exclude_features)
        profile_desc = "full"

    if args.exclude_features:
        profile_desc += f" (excluding: {', '.join(args.exclude_features)})"

    print(f"{Colors.YELLOW}Selected profile: {profile_desc} ({len(wanted_packages)} packages).{Colors.END}\n")

    device_props = fetch_device_props(serial)
    if device_props:
        print("Device information:")
        for k, v in device_props.items():
            print(f"  {k}: {v}")
        print()

    if mode == "debloat":
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

        print(f"\n{Colors.BOLD}{Colors.YELLOW}This action is non-destructive and can be reversed with --restore mode.{Colors.END}")

    else:  # restore mode
        packages = wanted_packages
        print("Packages that will be restored:")
        for pkg in packages:
            print(f"  - {pkg}")
        
        print(f"\n{Colors.BOLD}{Colors.YELLOW}This will attempt to restore the selected packages.{Colors.END}")

    if not args.yes:
        try:
            confirm = input(f"Proceed with {mode}? (y/n): ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print("\nOperation cancelled by user.")
            sys.exit(1)

        if confirm != 'y':
            print("Operation cancelled.")
            sys.exit(0)
    else:
        print(f"Auto-confirming {mode} operation (--yes flag used)")

    log_fp = None
    if args.log:
        ts = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        log_fp = open(f'{mode}_{ts}.log', 'w', encoding='utf-8')
        log_line(log_fp, f"Mode: {mode}")
        log_line(log_fp, f"Profile: {profile_desc}")
        log_line(log_fp, f"Device: {serial}")
        for k, v in device_props.items():
            log_line(log_fp, f"{k}: {v}")
        log_line(log_fp, '')

    if mode == "debloat":
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
        
        print(f"\n{Colors.BOLD}--- Debloat Finished ---{Colors.END}")
        print(f"{Colors.GREEN}Successfully uninstalled: {success_count}{Colors.END}")
        print(f"{Colors.YELLOW}Failed/not found: {fail_count}{Colors.END}")

    else:  # restore mode
        success_count, fail_count = restore_packages(serial, packages, args.dry_run, log_fp)
        
        print(f"\n{Colors.BOLD}--- Restore Finished ---{Colors.END}")
        print(f"{Colors.GREEN}Successfully restored: {success_count}{Colors.END}")
        print(f"{Colors.YELLOW}Already present/not found: {fail_count}{Colors.END}")

    if log_fp:
        log_fp.close()


if __name__ == '__main__':
    main()
