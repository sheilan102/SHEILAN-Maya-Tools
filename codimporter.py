#!/usr/bin/python
# -*- coding: utf-8 -*-
from functools import partial
import os
import os.path
import maya.cmds as cmds
import maya.mel as mel
import json
import logging
import SHEILAN_Tools

class CODMAP(object):
 
    def __init__(self):
        self.product = ''
        map_dest = SHEILAN_Tools.__importfile_dialog__(
            "MAP Folder", "Locate MAP directory", 3)
        xmodel_folder = SHEILAN_Tools.__importfile_dialog__(
            "XModel Folder", "Locate Greyhound's XModel directory", 3)
        if map_dest and xmodel_folder:
            map_name = map_dest.split("\\")
            map_name = map_name[len(map_name)-1]
            map_dest = map_dest + "\\" + map_name
            print(map_dest)
            print(xmodel_folder)
            print(map_name)
            self.importMap(map_dest,xmodel_folder,map_name)
        else:
            SHEILAN_Tools.__log_info__(False, "One or two of the necessary directories were not selected")


    def importMap(
        self,
        map_dest,
        xmodel_folder,
        mapname,
        ):
 
        # Load Model Properties
        json_models = open(map_dest + "_xmodels.json") 
        modeldata = json.load(json_models)

        # Model Count
        curAmount = 1
        badModels = []

        # Create groups for the loaded data
        cmds.group(em=True, name='xmodels')
        cmds.group(em=True, name=mapname + '_group')
        cmds.group(em=True, name='mapGeoemtry')
 
        # Import the map .obj fom Husky folder
        cmds.file(map_dest + '.obj', i=True)
 
        # Create a list of all geometry in the scene
        MapList = cmds.ls(geometry=True)
 
        # Parent each geoemtry into 'mapGeometry' group (no xmodels)
        for m in MapList:
            cmds.parent(m, 'mapGeoemtry')
 
        # Create .txt file with all bad models
        f_badmodels = open(map_dest + "_badModels.txt", "w")
        
        # Read XModels data
        for XModel in modeldata:
            # Load current XModel data from JSON
            if 'Name' in XModel:    
                self.addXModel(xmodel_folder, XModel, 1, badModels)

 
            # Loading progress
            print("loaded " + str(curAmount) + " of " + str(len(modeldata)))
            curAmount += 1
            #reporter = mel.eval('string $tmp = $gCommandReporter;')
            #cmds.cmdScrollFieldReporter(reporter, e=True, clear=True

        # Write all bad imports to file
        for b in badModels:
            f_badmodels.write(b)
        f_badmodels.close()
			
        # Delete all corrupted models & joints
        for o in cmds.ls(mat = False):
            if "|" not in o:
                if "Joints" in o or "LOD" in o:
                    try:
                        cmds.delete(o)
                    except:
                        print('')

        # Rescale mapGeo
        cmds.scale(0.3937007874015748,
                   0.3937007874015748,
                   0.3937007874015748,
                   'mapGeoemtry', absolute=True)
 
        # Group both xmodels & mapGeo to one final group
        cmds.parent('xmodels', mapname + '_group')
        cmds.parent('mapGeoemtry', mapname + '_group')
        cmds.polyColorSet( delete= True, colorSet= 'colorSet1')

        # Rescale the map to 0.01 because it's too damn huge
        cmds.scale(0.01, 0.01, 0.01, mapname + '_group', absolute=True)
 
        # Success
        print('imported %i models' % (len(modeldata)-(len(badModels))))
        print('%i corruputed models' % len(badModels))

 

    def addXModel(self, xmodel_folder, XModel, duplicates, badModels):
        good_model = True

        # Define model & fix it's name since Maya doesn't like some characters
        modelname = XModel['Name']
        if "/" in modelname:
            modelname = modelname.split("/")[1]
        if "@" in modelname:
            mayamodel = modelname.replace("@","_")
        else:
            mayamodel = modelname

        xmodelPos = [XModel['PosX'],XModel['PosY'],XModel['PosZ']]

        # Check if the model has Rotation values
        if 'RotX' in XModel:
            xmodelRot = [XModel['RotX'],XModel['RotY'],XModel['RotZ']]
        else:
            xmodelRot = 0,0,0
        
        # Check if model exists and duplicate, to avoid importing same model twice
        if cmds.objExists(mayamodel + '__%i' % duplicates) == True:
            # Go through duplicates untill there's an available name
            while cmds.objExists(mayamodel + '__%i'  % duplicates) == True:
                duplicates += 1
            
            # Duplicate last copy of the model
            cmds.duplicate(mayamodel + '__%i' % (duplicates-1))

        # If current XModel doesn't exist in the scene, load it
        else:
            # Import
            try:
                cmds.file(xmodel_folder + '\\' + modelname + '\\'
                            + modelname + '_LOD0.ma', i=True)
            except:
                good_model = False
                e = "import error"

            # Delete Joints
            try:
                # Delete XModel's joints
                cmds.delete('Joints')
            except:
                good_model = False
                e = "joints error"

            # Rename model
            try:
                # Rename model from modelname_LOD0 to modelname_DUPLICATENUMBER
                cmds.rename(modelname + '_LOD0', modelname + '__%i'
                            % duplicates)
            except:
                good_model = False
                e = "rename error"     

            # Parent to '_xmodels' group
            try:
                cmds.parent(modelname + '__%i' % duplicates, 'xmodels')

            except:
                good_model = False
                e = "parent error"        


        # Check if model was loaded succesfully into Maya
        if good_model:
            currentModel = modelname + '__%i' % duplicates

            # Move model
            cmds.move(float(xmodelPos[0]),
                        float(xmodelPos[1]),
                        float(xmodelPos[2]), currentModel,
                        absolute=True)

            # Rotate model
            cmds.rotate(float(xmodelRot[0]),
                        float(xmodelRot[1]),
                        float(xmodelRot[2]), currentModel,
                        absolute=True)
            
            # Scale model
            cmds.scale(float(XModel['Scale']) * 0.3937007874015748,
                        float(XModel['Scale']) * 0.3937007874015748,
                        float(XModel['Scale']) * 0.3937007874015748, currentModel,
                        absolute=True)

        # If model was not imported succesfully, add to '_badModels.txt' file
        if not good_model:
            if modelname not in badModels:
                badModels.append(modelname)
                badModels.append(e)
                badModels.append("\n")

        return badModels
