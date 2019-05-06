# SHEILAN's Maya Tools
Here's a small Maya plugin featuring every script I ever made for the program to automate long and annoying jobs.
All codes are made to make your life easier, so if something is bothering you, let me know and I shall fix it.


## Features

### COD
* Load FULL maps exported with [**C2M**](https://github.com/sheilan102/C2M).
* Import separated body parts into fullbody character.


## Installation & Usage

Download all .py files and place them in -

**64 Bit** `C:\Program Files\Autodesk\Maya-VER\bin\plug-ins`

**32 Bit** `C:\Program Files (x86)\Autodesk\Maya-VER\bin\plug-ins`

Launch Maya, go to `Window->Settings/Preferences->Plugin Manager`, look for `SHEILAN's Tools.py` and enable it.

#

#### Map Importer

1. Export MAP using C2M (above).
2. Go to exported MAP's folder, and open **`mp_mapname_xmodelList.txt`**.
3. Copy the search string as it is, and load Greyhound.
5. Set greyhound to load models only (preferrably), and export format to .SE.
6. Paste the search string you copied into the filter, and export all models.
7. Load Maya and proceed to importing the map (it's under SHEILAN's Tools).
8. Select MAP folder, then select Greyhound's xmodels folder (**e.g. `..\Greyhound\exported_files\black_ops_2\xmodels`**).


#### Loading fullbody character
1. Export your desired playermodel parts in **.MA format**.
2. Load fullbody character through 'SHEILAN' menu.
3. Choose your desired game (I only have acceess to the ones on the list, so if you export from games like IW, Ghosts, etc, then I suggest you first try using one of the two options, and if it won't work feel free to send me exported player parts and I'll add support.)
4. Hit load, and select the body parts in order (4 parts for BO3/4, 2 for others).
5. After model is imported, proceed to load all the `_BIND.mel` scripts to rig them (Will add an automatic option in future updates).

* After importing your second player to the scene, BIND scripts will give you error when trying to rig, because there will be more than one of each joint name, so what I suggest you to do is to `select all joint groups`, go to `Modify/Prefix Hierarchy Names` and select some prefix. Then you load the next BIND script, and rename them back through `Modify/Search & Replace Names` (search for whatever you wrote for prefix, and replace it with nothing).

## Changelog

***1.0.1***
* New fullbody import UI

***1.0.0***

* Initial Release

## Credit
I made those scripts as personal projects for myself and hopefully for other people who'll find good use in them.
Donations or credit aren't necessary but very appreciated! [![paypal](images/icon_paypal.svg)](https://paypal.me/ksheilan)

[![twitter](images/icon_twitter.svg)](https://twitter.com/SHEILANff)   [![youtube](images/icon_youtube.svg)](https://www.youtube.com/user/kalaboKKz)
