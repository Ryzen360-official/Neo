#!/bin/bash
set -euxo pipefail

#======================================
# Functions...
#--------------------------------------
test -f /.kconfig && . /.kconfig
test -f /.profile && . /.profile

#======================================
# Greeting...
#--------------------------------------
echo "Configure image: [$kiwi_iname]-[$kiwi_profiles]..."
setsebool -P selinuxuser_execmod 1

#======================================
# Core System Identity (Neo Linux Branding)
#--------------------------------------
cat << 'EOF' > /etc/os-release
NAME="Neo Linux"
VERSION="44"
ID=neo
ID_LIKE=fedora
VERSION_ID=44
PRETTY_NAME="Neo Linux 44"
ANSI_COLOR="0;36"
CPE_NAME="cpe:/o:neolinux:neo:44"
HOME_URL="https://github.com/Native-Neo"
BUG_REPORT_URL="https://github.com/Native-Neo/Neo/issues"
EOF
# =======================================================
# Configure systemd-boot as the default for kernel-install
# =======================================================
mkdir -p /etc/kernel
echo "layout=bls" > /etc/kernel/install.conf

# Tell the systemd boot management tool to initialize if needed downstream
mkdir -p /boot/efi
#======================================
# Clear machine specific configuration
#--------------------------------------
## Clear machine-id on pre generated images
rm -f /etc/machine-id
echo 'uninitialized' > /etc/machine-id
## remove random seed, the newly installed instance should make its own
rm -f /var/lib/systemd/random-seed

#======================================
# Configure grub correctly
#--------------------------------------
echo "GRUB_DEFAULT=saved" >> /etc/default/grub
## Disable submenus to match Fedora
echo "GRUB_DISABLE_SUBMENU=true" >> /etc/default/grub
## Disable recovery entries to match Fedora
echo "GRUB_DISABLE_RECOVERY=true" >> /etc/default/grub

#======================================
# Delete & lock the root user password
#--------------------------------------
passwd -d root
passwd -l root

#======================================
# KDE Plasma 6 Custom Global Branding
#======================================
# Ensure configuration directory paths exist
mkdir -p /etc/xdg

# Set default Global Theme
echo "PlasmaTheme=org.neo.theme" >> /etc/xdg/plasmarc

# Set default Wallpaper for Plasma 6 Shell
# We write this to the layout template to ensure liveuser and newly created users inherit it cleanly
mkdir -p /etc/xdg/plasma-workspace/env
cat << 'EOF' > /etc/xdg/plasma-org.kde.plasma.desktop-appletsrc
[Containments][1][Config]
Image=/usr/share/wallpapers/neo-1.jpg
EOF

#======================================
# Setup default services
#======================================
echo 'livesys_session="kde"' > /etc/sysconfig/livesys

#======================================
# Setup default target
#--------------------------------------
systemctl enable NetworkManager.service
systemctl set-default graphical.target
systemctl enable livesys.service
systemctl daemon-reload

#======================================
# Finalization steps
#--------------------------------------
# Inhibit the ldconfig cache generation unit, see rhbz2348669
touch -r "/usr" "/etc/.updated" "/var/.updated"

mkdir -p /etc/kernel
echo "BOOTLOADER=systemd-boot" >> /etc/sysconfig/kernel
mkdir -p /boot/efi
exit 0
