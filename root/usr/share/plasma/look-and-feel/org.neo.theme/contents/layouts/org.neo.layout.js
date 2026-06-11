var plasma = getApiVersion(1);

var panel = new Panel;
panel.location = "bottom";

var desktop = new Desktop;
desktop.wallpaperPlugin = "org.kde.image";
desktop.currentConfigGroup = ["Wallpaper", "org.kde.image", "General"];
desktop.writeConfig("Image", "file:///usr/share/wallpapers/neo-1.jpg");
