import argparse
import subprocess
import sys
import time

# ---------------------------------------------------------------------------
# THIRD-PARTY LAUNCHER HOME BUTTON LAG — WORKAROUND
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
# HOW IT WORKS:
#   1. Wakes the device and dismisses the keyguard (so UI automation works)
#   2. Launches the stock System Launcher via am start
#   3. Opens the recents/multitask view (KEYCODE_APP_SWITCH)
#   4. Locates the "System Launcher" card in recents using UI dump
#   5. Swipes the card up to dismiss it — this properly finishes the
#      launcher activity and removes the home-button interceptor
#   6. Returns to the third-party launcher home screen
#
# NOTE: The stock launcher CANNOT be fully disabled because the recents/
# multitask view (com.android.quickstep.RecentsActivity) is bundled inside
# it. This fix is therefore temporary — must be re-run after each reboot.
# For persistence, use an automation app (e.g. MacroDroid) with a boot
# trigger. Run with --setup-persist to configure this automatically.
#
# References:
#   - https://www.reddit.com/r/oneplus/comments/1p33lfj/
#   - https://xdaforums.com/t/4655464/page-13
# ---------------------------------------------------------------------------

MACRODROID_PKG = "com.arlosoft.macrodroid"


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
    print(f"{Colors.GREEN}Device {serial} found and authorized.{Colors.END}\n")
    return serial


def get_default_launcher(serial):
    cp = _shell(serial, 'cmd', 'package', 'resolve-activity', '--brief',
                '-c', 'android.intent.category.HOME',
                '-a', 'android.intent.action.MAIN')
    if cp.returncode == 0:
        for line in reversed(cp.stdout.strip().splitlines()):
            if '/' in line:
                return line.split('/')[0]
    return None


def get_nav_mode(serial):
    cp = _shell(serial, 'settings', 'get', 'secure', 'navigation_mode')
    if cp.returncode == 0:
        return cp.stdout.strip()
    return None


def get_ui_texts(serial):
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
    import re
    for text, cx, cy, x1, y1, x2, y2 in get_ui_texts(serial):
        if re.search(r'[Ss]ystem\s*[Ll]a', text):
            return (cx, cy, x1)
    return None


def setup_persist(serial):
    print(f"{Colors.BOLD}Setting up boot-persistent automation via MacroDroid...{Colors.END}\n")

    cp = _shell(serial, 'pm', 'list', 'packages', MACRODROID_PKG)
    if MACRODROID_PKG not in cp.stdout:
        print(f"{Colors.YELLOW}MacroDroid is not installed.{Colors.END}")
        print(f"Please install it from the Play Store first, then re-run this command.\n")
        print(f"  https://play.google.com/store/apps/details?id=com.arlosoft.macrodroid")
        return

    print(f"Granting permissions to MacroDroid...")
    _shell(serial, 'pm', 'grant', MACRODROID_PKG, 'android.permission.WRITE_SECURE_SETTINGS')
    _shell(serial, 'pm', 'grant', MACRODROID_PKG, 'android.permission.DUMP')
    _shell(serial, 'appops', 'set', MACRODROID_PKG, 'SYSTEM_ALERT_WINDOW', 'allow')
    _shell(serial, 'appops', 'set', MACRODROID_PKG, 'REQUEST_INSTALL_PACKAGES', 'allow')
    print(f"{Colors.GREEN}Permissions granted.{Colors.END}\n")

    print(f"{Colors.BOLD}Next steps (do this on your phone):{Colors.END}")
    print(f"  1. Open MacroDroid")
    print(f"  2. Create a new Macro:")
    print(f"     - Trigger: Device Boot")
    print(f"     - Action: Shell Script → enter this command:")
    print(f"         am start -n com.android.launcher/com.android.launcher.Launcher")
    print(f"       then add another Action:")
    print(f"     - Action: Shell Script → enter this command:")
    print(f"         am start -a com.android.launcher.action.CATEGORY_SETTINGS")
    print(f"  3. Save the macro and enable it")
    print(f"\n{Colors.YELLOW}Alternatively, a simpler one-shot approach:{Colors.END}")
    print(f"  Use a 'device boot' trigger with a single Shell Script action:")
    print(f"    am force-stop com.android.launcher")
    print(f"  (Note: this breaks recents until you manually launch a different app)")
    return


def main():
    parser = argparse.ArgumentParser(
        description="Fix third-party launcher home button lag on ColorOS 16 / realmeUI 6.0"
    )
    parser.add_argument('--setup-persist', action='store_true',
                        help='Set up MacroDroid boot automation for persistence')
    args = parser.parse_args()

    serial = check_adb_device()
    if not serial:
        sys.exit(1)

    if args.setup_persist:
        setup_persist(serial)
        return

    print(f"{Colors.BOLD}--- Third-Party Launcher Lag Fix ---{Colors.END}")
    print(f"{Colors.YELLOW}Temporary workaround — re-run after each reboot.{Colors.END}")
    print(f"{Colors.YELLOW}For persistence: python3 fix_launcher_lag.py --setup-persist{Colors.END}\n")

    default_launcher = get_default_launcher(serial)
    if default_launcher == 'com.android.launcher':
        print(f"{Colors.RED}Error: The stock System Launcher is set as default.")
        print(f"Please set a third-party launcher as default in Settings > Default Apps first.{Colors.END}")
        sys.exit(1)

    if default_launcher:
        print(f"Default launcher: {Colors.GREEN}{default_launcher}{Colors.END}")
    else:
        print(f"{Colors.YELLOW}Warning: Could not determine default launcher.{Colors.END}")

    nav_mode = get_nav_mode(serial)
    if nav_mode == '2':
        print(f"\n{Colors.RED}Warning: You are using gesture navigation.")
        print(f"This workaround only fixes the lag with 3-button navigation.{Colors.END}")
        try:
            confirm = input("Continue anyway? (y/n): ").strip().lower()
        except KeyboardInterrupt:
            print("\nCancelled.")
            sys.exit(1)
        if confirm != 'y':
            sys.exit(0)
    else:
        print(f"Navigation mode: {Colors.GREEN}3-button{Colors.END}")

    cp = _shell(serial, 'pm', 'list', 'packages', '-d')
    was_disabled = 'com.android.launcher' in cp.stdout
    if was_disabled:
        print(f"\n{Colors.YELLOW}System Launcher was disabled. Re-enabling...{Colors.END}")
        _shell(serial, 'pm', 'enable', 'com.android.launcher')

    print(f"\n{Colors.BOLD}Step 1/4:{Colors.END} Waking device and dismissing keyguard...")
    _shell(serial, 'input', 'keyevent', 'KEYCODE_POWER')
    time.sleep(0.5)
    _shell(serial, 'input', 'keyevent', 'KEYCODE_POWER')
    time.sleep(0.5)
    _shell(serial, 'wm', 'dismiss-keyguard')
    time.sleep(1)

    print(f"{Colors.BOLD}Step 2/4:{Colors.END} Launching stock System Launcher...")
    _shell(serial, 'am', 'start', '-n', 'com.android.launcher/com.android.launcher.Launcher')
    time.sleep(2)

    cp = _shell(serial, 'dumpsys', 'activity', 'activities')
    if 'com.android.launcher/.Launcher' not in cp.stdout:
        print(f"{Colors.YELLOW}Stock launcher didn't start. Trying fallback...{Colors.END}")
        _shell(serial, 'am', 'start', '-a', 'android.intent.action.MAIN',
               '-n', 'com.android.launcher/com.android.launcher.Launcher')
        time.sleep(2)

    print(f"{Colors.BOLD}Step 3/4:{Colors.END} Opening recents and dismissing System Launcher...")
    _shell(serial, 'input', 'keyevent', 'KEYCODE_APP_SWITCH')
    time.sleep(2)

    launcher_coords = find_system_launcher_in_recents(serial)

    if launcher_coords:
        cx, cy, x1 = launcher_coords
        screen_mid = 540
        if x1 > screen_mid:
            _shell(serial, 'input', 'swipe', '900', '800', '200', '800', '300')
            time.sleep(1)
            launcher_coords = find_system_launcher_in_recents(serial)

    if not launcher_coords:
        _shell(serial, 'input', 'swipe', '900', '800', '200', '800', '300')
        time.sleep(1)
        launcher_coords = find_system_launcher_in_recents(serial)

    if launcher_coords:
        cx, cy, _ = launcher_coords
        _shell(serial, 'input', 'swipe', str(cx), '800', str(cx), '0', '150')
        time.sleep(0.5)
        print(f"{Colors.GREEN}System Launcher card dismissed from recents.{Colors.END}")
    else:
        print(f"{Colors.YELLOW}Could not find System Launcher card automatically.")
        print(f"Manually swipe it away from recents, then press Enter.{Colors.END}")
        try:
            input()
        except EOFError:
            pass

    print(f"{Colors.BOLD}Step 4/4:{Colors.END} Returning to home screen...")
    _shell(serial, 'input', 'keyevent', 'KEYCODE_HOME')
    time.sleep(0.5)

    print(f"\n{Colors.GREEN}{Colors.BOLD}Done!{Colors.END}")
    print(f"{Colors.GREEN}Home button lag should now be gone.{Colors.END}")
    print(f"\n{Colors.YELLOW}Temporary only — re-run after each reboot.{Colors.END}")
    print(f"To make it persistent: python3 fix_launcher_lag.py --setup-persist")
    print(f"Once Oplus ships the proper fix in a realmeUI update,")
    print(f"this script will no longer be needed.{Colors.END}")


if __name__ == '__main__':
    main()
