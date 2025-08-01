# Realme GT 6 Debloater

This repository contains a set of Python scripts designed to safely remove bloatware from the Realme GT 6 (Global/EU Version) running Realme UI 5.0.

The primary method used is ADB (`pm uninstall --user 0`), which uninstalls applications for the current user only. This method does not require root and is non-destructive, meaning any changes can be fully reverted via the included reinstallation script or a factory reset.

## Scripts

This project includes two main scripts:

*   `debloat_gt6.py`: The main debloating script. It removes a curated list of non-essential manufacturer apps and advertising services.
*   `reinstall_gt6.py`: A safety script that reinstalls all packages removed by the debloater script, effectively undoing the changes.

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

4.  Run the debloating script:
    ```bash
    python3 debloat_gt6.py
    ```
    The script will display a list of packages to be removed and ask for a final confirmation before proceeding.

5.  (Optional) To undo all changes, run the reinstallation script:
    ```bash
    python3 reinstall_gt6.py
    ```

## Disclaimer

These scripts are provided as-is. While they are designed to be safe, you are responsible for the actions you perform on your device. The list of packages to be removed has been curated for a standard user experience, but you can edit the Python scripts to add or remove packages according to your specific needs.
