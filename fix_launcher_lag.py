# Standard library imports
import subprocess
import sys
import time

# ---------------------------------------------------------------------------
# TEMPORARY WORKAROUND — Third-party launcher home button lag
# ---------------------------------------------------------------------------
# Affects:  ColorOS 16 / realmeUI 6.0 / OxygenOS 16 (all Oplus devices)
# Root cause: The stock System Launcher (com.android.launcher) keeps running
#             in the background even when a third-party launcher is set as
#             default. Every home-button press briefly routes through the
#             stock launcher before reaching the third-party one, causing a
#             visible lag/stutter.
# Scope:     Only affects 3-button navigation. Gesture navigation remains
#             broken with third-party launchers on these OS versions.
# Expected fix: Oplus has started fixing this in OxygenOS 16.0.3.501+.
#             Once ColorOS / realmeUI ships an equivalent patch, this script
#             will no longer be necessary.
#
# What this script does (Reddit / XDA workaround, automated via ADB):
#   1. Opens Settings > Home screen settings > Transition animations.
#   2. Tapping that setting triggers an OS bug that kicks the user to the
#      stock System Launcher home screen instead of showing the setting.
#   3. The script then opens the recents view, locates the System Launcher
#      card, and swipes it away.
#   4. This stops the stock launcher from intercepting home-button presses.
#
# Limitations:
#   - Must be repeated after every reboot or whenever the stock launcher
#     is inadvertently started.
#   - Does NOT work with gesture navigation (only 3-button nav).
#
# References:
#   - https://www.reddit.com/r/oneplus/comments/1p33lfj/
#   - https://xdaforums.com/t/4655464/page-13
# ---------------------------------------------------------------------------


class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'


def _run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def _shell(serial, *args):
    return _run(['adb', '-s', serial, 'shell'] + list(args))


def check_adb_device():
    try:
        result = subprocess.run(['adb', 'devices'], capture_output=True, text=True, check=True)
    except FileNotFoundError:
        print(f"{Colors.RED}Error: 'adb' command not found in PATH.{Colors.END}")
        return None
    except subprocess.CalledProcessError:
        print(f"{Colors.RED}Error: 'adb devices' failed.{Colors.END}")
        return None

    lines = [l for l in result.stdout.strip().split('\n') if l.strip()]
    lines = [l for l in lines if not l.lower().startswith('list of devices')]

    if len(lines) != 1 or not lines[0].endswith('\tdevice'):
        print(f"{Colors.RED}Error: Exactly one authorized device required but {len(lines)} found.{Colors.END}")
        return None

    serial = lines[0].split('\t')[0]
    print(f"{Colors.GREEN}✔ Device {serial} found and authorized.{Colors.END}\n")
    return serial


def get_default_launcher(serial):
    """Return the package name of the current default launcher."""
    cp = _shell(serial, 'cmd', 'package', 'resolve-activity', '--brief',
                '-c', 'android.intent.category.HOME',
                '-a', 'android.intent.action.MAIN')
    if cp.returncode == 0:
        # Last line is like: ginlemon.flowerfree/ginlemon.flower.HomeScreen
        for line in reversed(cp.stdout.strip().splitlines()):
            if '/' in line:
                return line.split('/')[0]
    return None


def get_nav_mode(serial):
    """Return navigation mode: 0 = 3-button, 2 = gesture."""
    cp = _shell(serial, 'settings', 'get', 'secure', 'navigation_mode')
    if cp.returncode == 0:
        return cp.stdout.strip()
    return None


def get_ui_bounds(serial, text):
    """Dump UI hierarchy and return (cx, cy) center of element matching text."""
    _shell(serial, 'uiautomator', 'dump', '/sdcard/ui_dump.xml')
    cp = _shell(serial, 'cat', '/sdcard/ui_dump.xml')
    if cp.returncode != 0:
        return None

    import re
    # Find element with matching text and extract bounds
    pattern = rf'text="{re.escape(text)}"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"'
    match = re.search(pattern, cp.stdout)
    if match:
        x1, y1, x2, y2 = int(match.group(1)), int(match.group(2)), int(match.group(3)), int(match.group(4))
        return ((x1 + x2) // 2, (y1 + y2) // 2)
    return None


def find_system_launcher_in_recents(serial):
    """Look for the System Launcher card in recents and return its center coords."""
    # Try common label variations
    for label in ["System La...", "System Launcher", "System La…"]:
        coords = get_ui_bounds(serial, label)
        if coords:
            return coords

    # Fallback: look for anything from com.android.launcher in the UI
    _shell(serial, 'uiautomator', 'dump', '/sdcard/ui_dump.xml')
    cp = _shell(serial, 'cat', '/sdcard/ui_dump.xml')
    if cp.returncode == 0:
        import re
        match = re.search(r'text="[^"]*[Ss]ystem\s*[Ll]a[^"]*"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', cp.stdout)
        if match:
            x1, y1, x2, y2 = int(match.group(1)), int(match.group(2)), int(match.group(3)), int(match.group(4))
            return ((x1 + x2) // 2, (y1 + y2) // 2)
    return None


def main():
    print(f"{Colors.BOLD}--- Third-Party Launcher Lag Fix (Temporary Workaround) ---{Colors.END}")
    print(f"{Colors.YELLOW}This fix is needed on ColorOS 16 / realmeUI 6.0 / OxygenOS 16.")
    print(f"It should become unnecessary once Oplus patches the OS.{Colors.END}\n")

    serial = check_adb_device()
    if not serial:
        sys.exit(1)

    # --- Pre-flight checks ---

    # Check that a third-party launcher is set as default
    default_launcher = get_default_launcher(serial)
    if default_launcher == 'com.android.launcher':
        print(f"{Colors.RED}Error: The stock System Launcher is set as default.")
        print(f"Please set a third-party launcher as default in Settings > Default Apps first.{Colors.END}")
        sys.exit(1)

    if default_launcher:
        print(f"Default launcher: {Colors.GREEN}{default_launcher}{Colors.END}")
    else:
        print(f"{Colors.YELLOW}Warning: Could not determine default launcher. Proceeding anyway.{Colors.END}")

    # Check navigation mode
    nav_mode = get_nav_mode(serial)
    if nav_mode == '2':
        print(f"\n{Colors.RED}Warning: You are using gesture navigation.")
        print(f"This workaround only fixes the lag with 3-button navigation.")
        print(f"Consider switching to 3-button navigation for a lag-free experience.{Colors.END}")
        try:
            confirm = input("Continue anyway? (y/n): ").strip().lower()
        except KeyboardInterrupt:
            print("\nCancelled.")
            sys.exit(1)
        if confirm != 'y':
            sys.exit(0)
    else:
        print(f"Navigation mode: {Colors.GREEN}3-button{Colors.END}")

    # Check the system launcher is enabled (required for recents to work)
    cp = _shell(serial, 'pm', 'list', 'packages', '-d')
    if 'com.android.launcher' in cp.stdout:
        print(f"\n{Colors.YELLOW}System Launcher is currently disabled. Re-enabling it first...{Colors.END}")
        _shell(serial, 'pm', 'enable', 'com.android.launcher')

    print(f"\n{Colors.BOLD}Step 1/4:{Colors.END} Opening Home screen settings...")
    # Navigate to Home screen settings where "Transition animations" lives
    _shell(serial, 'am', 'start', '-a', 'android.intent.action.MAIN',
           '-n', 'com.android.launcher/com.android.launcher.SettingsActivity')
    time.sleep(1)

    # If the above doesn't work, try via system settings search
    # Open Settings and search for "Transition animations"
    _shell(serial, 'am', 'start', '-a', 'android.settings.SETTINGS')
    time.sleep(1)

    # Navigate to: Home Screen, Lock screen & style > Home screen settings
    coords = get_ui_bounds(serial, "Transition animations")
    if not coords:
        # Try navigating through settings manually
        _shell(serial, 'am', 'start', '-a', 'android.settings.SETTINGS')
        time.sleep(1)
        hs_coords = get_ui_bounds(serial, "Home screen, Lock screen & style")
        if hs_coords:
            _shell(serial, 'input', 'tap', str(hs_coords[0]), str(hs_coords[1]))
            time.sleep(1)
            hss_coords = get_ui_bounds(serial, "Home screen settings")
            if hss_coords:
                _shell(serial, 'input', 'tap', str(hss_coords[0]), str(hss_coords[1]))
                time.sleep(1)
        coords = get_ui_bounds(serial, "Transition animations")

    if not coords:
        print(f"{Colors.RED}Error: Could not find 'Transition animations' setting.")
        print(f"Try navigating manually to: Settings > Home Screen, Lock screen & style")
        print(f"> Home screen settings > Transition animations{Colors.END}")
        sys.exit(1)

    print(f"{Colors.BOLD}Step 2/4:{Colors.END} Tapping 'Transition animations' to trigger stock launcher...")
    _shell(serial, 'input', 'tap', str(coords[0]), str(coords[1]))
    time.sleep(1.5)

    # Verify we landed on the stock launcher (not the actual setting screen)
    cp = _shell(serial, 'dumpsys', 'activity', 'activities')
    if 'com.android.launcher/.Launcher' not in cp.stdout:
        print(f"{Colors.YELLOW}Note: The stock launcher may not have been triggered.")
        print(f"If you see the Transition animations setting screen instead,")
        print(f"this bug may already be fixed in your OS version.{Colors.END}")

    print(f"{Colors.BOLD}Step 3/4:{Colors.END} Opening recents and dismissing System Launcher...")
    _shell(serial, 'input', 'keyevent', 'KEYCODE_APP_SWITCH')
    time.sleep(1)

    # Find and swipe away the System Launcher card
    launcher_coords = find_system_launcher_in_recents(serial)

    if launcher_coords:
        # First make sure the card is centered (tap on it or swipe to it)
        _shell(serial, 'input', 'tap', str(launcher_coords[0]), str(launcher_coords[1]))
        time.sleep(0.5)

        # If the card isn't in the center, swipe left in recents to find it
        _shell(serial, 'input', 'keyevent', 'KEYCODE_APP_SWITCH')
        time.sleep(1)

    # Try to find it again in recents
    launcher_coords = find_system_launcher_in_recents(serial)
    if not launcher_coords:
        # Swipe left in recents to look for it
        _shell(serial, 'input', 'swipe', '800', '800', '200', '800', '300')
        time.sleep(0.5)
        launcher_coords = find_system_launcher_in_recents(serial)

    if launcher_coords:
        # Swipe up aggressively to dismiss
        cx = str(launcher_coords[0])
        _shell(serial, 'input', 'swipe', cx, '800', cx, '0', '150')
        time.sleep(0.5)
        print(f"{Colors.GREEN}System Launcher card dismissed from recents.{Colors.END}")
    else:
        print(f"{Colors.YELLOW}Could not find System Launcher in recents automatically.")
        print(f"Please manually swipe away the 'System Launcher' card from recents.{Colors.END}")
        input("Press Enter once done...")

    print(f"{Colors.BOLD}Step 4/4:{Colors.END} Returning to home screen...")
    _shell(serial, 'input', 'keyevent', 'KEYCODE_HOME')
    time.sleep(0.5)

    print(f"\n{Colors.GREEN}{Colors.BOLD}Done!{Colors.END}")
    print(f"{Colors.GREEN}The home button lag should now be gone.{Colors.END}")
    print(f"\n{Colors.YELLOW}Reminder: This fix is temporary and must be repeated after each reboot.")
    print(f"Once your OS is updated to a patched version, this will no longer be needed.{Colors.END}")


if __name__ == '__main__':
    main()
