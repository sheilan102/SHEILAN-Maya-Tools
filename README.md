# SHEILAN's Maya Tools
Here's a small Maya plugin featuring every script I ever made for the program mostly to automate long and annoying jobs.
All codes are made to make your life easier, so if something is bothering you, let me know and I shall fix it.


## Features

### COD
* Load FULL maps exported with Husky ([updated version](https://github.com/sheilan102/husky_modified)).
* Combine separated body models into one, fullbody skeleton (supporting only BO4 currently).



## Installation & Usage

Download all .py files and place them in -

**64 Bit** `C:\Program Files\Autodesk\Maya2018\bin\plug-ins`

**32 Bit** `C:\Program Files (x86)\Autodesk\Maya2018\bin\plug-ins`

Launch Maya, go to `Window->Settings/Preferences->Plugin Manager`, look for `SHEILAN's Tools.py` and enable it.

#

#### Map Importer

1. Export MAP using husky_modified (above).
2. Go to exported MAP's folder, and open **`mp_mapname_xmodelList.txt`**.
3. Copy the search string as it is, and load Greyhound.
5. Set greyhound to load models only (preferrably), and export format to .SE.
6. Paste the search string you copied into the filter, and export all models.
7. Load Maya and proceed to importing the map (it's under SHEILAN's Tools).
8. Select MAP folder, then select Greyhound's xmodels folder (**e.g. `..\Greyhound\exported_files\black_ops_2\xmodels`**).
