#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# === This file is part of Calamares - <https://calamares.io> ===
#
# Custom systemd-boot module optimized explicitly for Fedora bases.
# Hardcodes the target ESP paths to safely step over globalstorage parsing bugs.
#

import os
import subprocess
import libcalamares
import gettext

_ = gettext.translation("calamares-python",
                        localedir=libcalamares.utils.gettext_path(),
                        languages=libcalamares.utils.gettext_languages(),
                        fallback=True).gettext

def pretty_name():
    return _("Installing systemd-boot...")

def run_cmd_in_chroot(root_path, cmd):
    """
    Helper to execute commands smoothly within the target installation.
    """
    chroot_cmd = ["chroot", root_path] + cmd
    libcalamares.utils.debug(f"Executing: {' '.join(chroot_cmd)}")
    return subprocess.call(chroot_cmd)

def get_root_cmdline_params(target_root):
    """
    Extract the root partition identifier and optional BTRFS subvolume from target /etc/fstab
    to generate correct kernel boot parameters.
    """
    fstab_path = os.path.join(target_root, "etc", "fstab")
    if not os.path.exists(fstab_path):
        return "ro quiet"

    root_device = None
    root_fstype = None
    root_options = None

    try:
        with open(fstab_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split()
                if len(parts) >= 4 and parts[1] == "/":
                    root_device = parts[0]
                    root_fstype = parts[2]
                    root_options = parts[3]
                    break
    except Exception as e:
        libcalamares.utils.warning(f"Failed to read target /etc/fstab: {str(e)}")
        return "ro quiet"

    if not root_device:
        return "ro quiet"

    cmdline_parts = [f"root={root_device}"]

    # Handle BTRFS subvolume if applicable
    if root_fstype == "btrfs" and root_options:
        subvol = None
        for opt in root_options.split(","):
            if opt.startswith("subvol="):
                subvol = opt
                break
        if subvol:
            cmdline_parts.append(f"rootflags={subvol}")

    cmdline_parts.extend(["ro", "quiet"])
    return " ".join(cmdline_parts)

def run():
    # 1. Grab the target root path
    target_root = libcalamares.globalstorage.value("rootMountPoint")

    if not target_root or not os.path.exists(target_root):
        libcalamares.utils.warning("Target root mount point could not be found.")
        return (_("Bootloader Error"), _("Target system root path is missing."))

    # Verify we are booted into an EFI environment
    if not os.path.exists("/sys/firmware/efi"):
        return (_("Environment Error"), _("System is not booted in UEFI mode; systemd-boot cannot be initialized."))

    try:
        libcalamares.utils.debug("Initializing systemd-boot installation routines...")

        # 2. Purge standard Fedora GRUB packages to prevent post-install execution blocks
        libcalamares.utils.debug("Removing conflicting GRUB tracking utilities...")
        run_cmd_in_chroot(target_root, ["rm", "-f", "/etc/dnf/protected.d/grub*"])

        # 3. Initialize systemd-boot binaries into the ESP
        # Fedora generally prefers /boot or /efi depending on configuration, we target standard /boot/efi
        libcalamares.utils.debug("Running bootctl install...")
        bootctl_rc = run_cmd_in_chroot(target_root, ["bootctl", "--esp-path=/boot/efi", "install"])
        if bootctl_rc != 0:
            libcalamares.utils.warning("bootctl install reported an execution error.")

        # 4. Enforce Fedora layout requirements inside kernel/install.conf
        kernel_conf_dir = os.path.join(target_root, "etc", "kernel")
        os.makedirs(kernel_conf_dir, exist_ok=True)
        with open(os.path.join(kernel_conf_dir, "install.conf"), "w") as f:
            f.write("layout=bls\n")

        # Determine and write correct persistent kernel parameters to etc/kernel/cmdline
        # This prevents systemd-boot from falling back to /proc/cmdline (which has live-media params)
        cmdline_str = get_root_cmdline_params(target_root)
        libcalamares.utils.debug(f"Writing kernel command line parameters: {cmdline_str}")
        with open(os.path.join(kernel_conf_dir, "cmdline"), "w") as f:
            f.write(f"{cmdline_str}\n")

        # 5. Automatically detect and propagate installed kernels into systemd-boot BLS entries
        # This matches Fedora's native 'kernel-install' hooks
        modules_path = os.path.join(target_root, "usr", "lib", "modules")
        if os.path.exists(modules_path):
            kernels = [d for d in os.listdir(modules_path) if os.path.isdir(os.path.join(modules_path, d))]
            for kver in kernels:
                vmlinuz_target = f"/usr/lib/modules/{kver}/vmlinuz"
                if os.path.exists(os.path.join(target_root, vmlinuz_target.lstrip("/"))):
                    libcalamares.utils.debug(f"Registering kernel version: {kver}")
                    run_cmd_in_chroot(target_root, ["kernel-install", "add", kver, vmlinuz_target])

    except Exception as e:
        libcalamares.utils.warning(f"Exception triggered during systemd-boot deployment: {str(e)}")
        return (_("systemd-boot Exception"), str(e))

    # Return None to signal smooth completion
    return None
