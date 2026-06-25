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
#   1. Directly launches the stock System Launcher via am start.
#   2. Opens the recents view and locates the System Launcher card.
#   3. Swipes the card left into view (if needed) and swipes it up to dismiss.
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


def get_ui_texts(serial):
    """Dump UI hierarchy and return list of (text, cx, cy, x1, y1, x2, y2)."""
    import re
    _shell(serial, 'uiautomator', 'dump', '/sdcard/ui_dump.xml')
    cp = _shell(serial, 'cat', '/sdcard/ui_dump.xml')
    if cp.returncode != 0:
        return []
    results = []
    for m in re.finditer(
        r'<node[^>]*text="([^"]+)"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', cp.stdout
    ):
        text = m.group(1)
        x1, y1, x2, y2 = int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5))
        results.append((text, (x1 + x2) // 2, (y1 + y2) // 2, x1, y1, x2, y2))
    return results


def find_system_launcher_in_recents(serial):
    """Look for the System Launcher card in recents and return (cx, cy, x1)."""
    import re
    for text, cx, cy, x1, y1, x2, y2 in get_ui_texts(serial):
        if re.search(r'[Ss]ystem\s*[Ll]a', text):
            return (cx, cy, x1)
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

    print(f"\n{Colors.BOLD}Step 1/3:{Colors.END} Launching stock System Launcher...")
    _shell(serial, 'am', 'start', '-n', 'com.android.launcher/com.android.launcher.Launcher')
    time.sleep(1.5)

    cp = _shell(serial, 'dumpsys', 'activity', 'activities')
    if 'com.android.launcher/.Launcher' not in cp.stdout:
        print(f"{Colors.YELLOW}Warning: Stock launcher may not have started. Trying fallback...{Colors.END}")
        _shell(serial, 'am', 'start', '-a', 'android.intent.action.MAIN',
               '-n', 'com.android.launcher/com.android.launcher.Launcher')
        time.sleep(1.5)

    print(f"{Colors.BOLD}Step 2/3:{Colors.END} Opening recents and dismissing System Launcher...")
    _shell(serial, 'input', 'keyevent', 'KEYCODE_APP_SWITCH')
    time.sleep(1.5)

    launcher_coords = find_system_launcher_in_recents(serial)

    if launcher_coords:
        cx, cy, x1 = launcher_coords
        # If the card is at the screen edge, swipe left to bring it into view
        screen_mid = 540
        if x1 > screen_mid:
            _shell(serial, 'input', 'swipe', '900', '800', '200', '800', '300')
            time.sleep(1)
            launcher_coords = find_system_launcher_in_recents(serial)

    if not launcher_coords:
        # Swipe left in recents to look for it
        _shell(serial, 'input', 'swipe', '900', '800', '200', '800', '300')
        time.sleep(1)
        launcher_coords = find_system_launcher_in_recents(serial)

    if launcher_coords:
        cx, cy, _ = launcher_coords
        _shell(serial, 'input', 'swipe', str(cx), '800', str(cx), '0', '150')
        time.sleep(0.5)
        print(f"{Colors.GREEN}System Launcher card dismissed from recents.{Colors.END}")
    else:
        print(f"{Colors.YELLOW}Could not find System Launcher in recents automatically.")
        print(f"Please manually swipe away the 'System Launcher' card from recents.{Colors.END}")
        input("Press Enter once done...")

    print(f"{Colors.BOLD}Step 3/3:{Colors.END} Returning to home screen...")
    _shell(serial, 'input', 'keyevent', 'KEYCODE_HOME')
    time.sleep(0.5)

    print(f"\n{Colors.GREEN}{Colors.BOLD}Done!{Colors.END}")
    print(f"{Colors.GREEN}The home button lag should now be gone.{Colors.END}")
    print(f"\n{Colors.YELLOW}Reminder: This fix is temporary and must be repeated after each reboot.")
    print(f"Once your OS is updated to a patched version, this will no longer be needed.{Colors.END}")


if __name__ == '__main__':
    main()
