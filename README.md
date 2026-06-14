# Neo Linux
- Install Deps first: sudo dnf kiwi-cli qemu-img kpartx btrfs-progs implantisomd5 mkfs.fat squashfs-tools xorriso -y
- You can choose from Core, Hyper-Nova, Game-Nova, Dev-Nova!
- Build Command : sudo rm -rf ./out/ && sudo kiwi-ng --kiwi-file ./Fedora.kiwi --shared-cache-dir ./cache --profile=replace-me-with-one-from-above --debug system build   --description ./   --target-dir ./out

### NOTE:: THIS DISTRO IS Fedora Based NOT Fedora
