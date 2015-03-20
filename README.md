Blender Add-on with Verse Integration
=====================================

This is alpha version of Blender Python Add-on with Verse integration. It is
possible to share Mesh objects at Verse server now.

![Blender Verse Add-on screenshot](/screenshots/blender-verse-screenshot.png "Verse Blender Add-on screenshot")

### Requirements ###

This Add-on requires Blender 2.76 and Python module called Verse that could be
found here:

http://verse.github.com/verse/

Verse project contains compiled Python module and only Linux OS is supported now.

### Installation ###

To install this Add-on download file:

https://github.com/verse/verse-blender/archive/master.zip

Unzip this archive and move directory io_verse to directory with your add-ons.
Typically ~/.config/blender/2.68a/scripts/addons/

You can also download current version using git:

    git clone git@github.com:verse/verse-blender.git
    cd verse-blender
    git submodule update --init --recursive
    git submodule foreach --recursive git checkout master
    git submodule foreach --recursive git pull --rebase origin master

To update verse-blender to current version run following commands:

    git pull --rebase
    git submodule foreach --recursive git pull --rebase origin master

### License ###

The source code of this Blender Add-on is available under GNU GPL 2.0. For details
look at LICENSE file.

