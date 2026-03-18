# Realme GT 6 Debloater

This repository contains a set of Python scripts designed to safely remove bloatware from the Realme GT 6 (Global/EU Version) running Realme UI 5.0+.

The primary method used is ADB (`pm uninstall --user 0`), which uninstalls applications for the current user only. This method does not require root and is non-destructive, meaning any changes can be fully reverted via the included reinstallation script or a factory reset.

## Scripts

*   `debloat_gt6.py`: The main debloating script. It removes a curated list of non-essential manufacturer apps and advertising services.
*   `reinstall_gt6.py`: A safety script that reinstalls all packages removed by the debloater script, effectively undoing the changes.
*   `fix_launcher_lag.py`: **[Temporary]** Fixes the home button lag when using a third-party launcher on ColorOS 16 / realmeUI 6.0. See [Third-Party Launcher Lag Fix](#third-party-launcher-lag-fix) below.

## Prerequisites

1.  **Python 3:** The scripts are written in Python and need to be executed with a Python 3 interpreter.
2.  **ADB Platform Tools:** You must have the official Google ADB Platform Tools installed and accessible in your system's PATH.
3.  **USB Debugging Enabled:** On your Realme GT 6, you must enable Developer Options and turn on USB Debugging.

## Usage

1.  Clone this repository to your local machine:
    ```bash
    git clone https://github.com/your-username/realme-gt6-debloater.git
    cd realme-gt6-debloater
    ```

2.  Connect your Realme GT 6 to your computer via USB. Authorize the USB debugging connection on the phone's screen when prompted.

3.  Verify the device is connected and authorized:
    ```bash
    adb devices
    ```

4.  Run the debloating script (default = full profile):
    ```bash
    python3 debloat_gt6.py            # full (safe + advanced) packages
    python3 debloat_gt6.py -m         # minimal profile (safe only)
    python3 debloat_gt6.py -n         # dry-run, show what would happen
    python3 debloat_gt6.py -l         # write a timestamped log file
    ```
    The script shows device information, lists packages that are *actually* still installed, skips the rest, and then asks for confirmation before acting.

5.  (Optional) To undo all changes, run the reinstallation script:
    ```bash
    python3 reinstall_gt6.py
    ```

## Third-Party Launcher Lag Fix

> **This is a temporary workaround.** The underlying bug exists in ColorOS 16 / realmeUI 6.0 / OxygenOS 16. OnePlus has started rolling out a fix in OxygenOS 16.0.3.501+. Once Realme ships an equivalent update, this script will no longer be needed.

### The problem

On ColorOS 16 (and OxygenOS 16), the stock System Launcher (`com.android.launcher`) keeps running in the background even when a third-party launcher (Nova, Smart Launcher, Niagara, etc.) is set as default. Every home button press briefly routes through the stock launcher before reaching your chosen one, causing a visible lag/stutter of ~0.5-1 second.

This affects **all Oplus devices** (Realme, OnePlus, Oppo) running these OS versions.

### What the fix does

The script automates a community-discovered workaround ([Reddit](https://www.reddit.com/r/oneplus/comments/1p33lfj/), [XDA](https://xdaforums.com/t/4655464/page-13)):

1. Opens **Settings > Home screen settings > Transition animations**
2. Tapping that setting triggers an OS bug that kicks the UI to the stock launcher home screen (instead of showing the actual setting)
3. Opens the **recents view**, finds the **System Launcher** card, and **swipes it away**
4. Returns to the third-party launcher home screen — lag is gone

### Limitations

- **3-button navigation only** — gesture navigation lag is NOT fixed by this workaround
- **Must be repeated after every reboot** or whenever the stock launcher is inadvertently started
- The stock launcher package cannot be fully disabled because the recents/multitask view (`com.android.quickstep.RecentsActivity`) is bundled inside it

### Usage

```bash
python3 fix_launcher_lag.py
```

Make sure your third-party launcher is already set as default in **Settings > Default Apps** before running.

### When will this be fixed permanently?

OnePlus confirmed a fix in OxygenOS 16.0.3.501 (reported working on OnePlus 13). Since Realme, OnePlus, and Oppo share the same ColorOS/OxygenOS codebase, the fix should eventually reach all devices. Check your OS version — if you're on a version newer than the fix, try rebooting without running this script to see if the issue is resolved.

## Disclaimer

These scripts are provided as-is. While they are designed to be safe, you are responsible for the actions you perform on your device. The list of packages to be removed has been curated for a standard user experience, but you can edit the Python scripts to add or remove packages according to your specific needs.
