# SHEILAN's Maya Tools
Here's a small Maya plugin featuring every script I ever made for the program to automate long and annoying jobs.
All codes are made to make your life easier, so if something is bothering you, let me know and I shall fix it.


## Features

### COD
* Load FULL maps exported with Husky ([modified version](https://github.com/sheilan102/husky_modified)).
* Combine separated body parts into one, fullbody skeleton (supporting only BO4 currently).

### Apex Legends
* Create HumanIK for Apex characters


## Installation & Usage

Download all .py files and place them in -

**64 Bit** `C:\Program Files\Autodesk\Maya2018\bin\plug-ins`

**32 Bit** `C:\Program Files (x86)\Autodesk\Maya2018\bin\plug-ins`

Launch Maya, go to `Window->Settings/Preferences->Plugin Manager`, look for `SHEILAN's Tools.py` and enable it.

* To use MAP Importer you need to install [DTZxPorter's SETools plugin](https://github.com/dtzxporter/SETools).
#

#### Map Importer

1. Export MAP using husky_modified (above).
2. Go to exported MAP's folder, and open **`mp_mapname_xmodelList.txt`**.
3. Copy the search string as it is, and load Greyhound.
5. Set greyhound to load models only (preferrably), and export format to .SE.
6. Paste the search string you copied into the filter, and export all models.
7. Load Maya and proceed to importing the map (it's under SHEILAN's Tools).
8. Select MAP folder, then select Greyhound's xmodels folder (**e.g. `..\Greyhound\exported_files\black_ops_2\xmodels`**).


#### Combining body parts
1. Export your desired playermodel parts in **.MA format** (Torso, Legs, Arms & Head).
2. Load each .MA file in Maya (without using the bind script yet).
3. Rename all groups to look like this (**LOD0** to **mesh**, and **Joints** to **skeleton**)/

![playerbody setup](images/playermodelexample.png)

4. Run the script and you should have 4 `_mesh` groups and 1 `fullbody_skeleton` group.
5. Now you proceed to loading the bind scripts (4 total).

## Changelog

***V** 1.00*

* Release

## Credit
I made those scripts as personal projects for myself and hopefully for other people who'll find good use in them.
Donations or credit aren't necessary but very appreciated! [![paypal](images/icon_paypal.svg)](https://paypal.me/ksheilan)

[![twitter](images/icon_twitter.svg)](https://twitter.com/SHEILANff)   [![youtube](images/icon_youtube.svg)](https://www.youtube.com/user/kalaboKKz)
