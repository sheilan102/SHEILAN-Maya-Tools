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
            # try:
            #     self.importMap(map_dest,xmodel_folder,map_name)
            #     SHEILAN_Tools.__log_info__(True, "Map imported succesfully")
            # except:
            #     SHEILAN_Tools.__log_info__(False, "Wrong directory selected")
        else:
            SHEILAN_Tools.__log_info__(False, "One or two of the necessary directories were not selected")


    def importMap(
        self,
        map_dest,
        xmodel_folder,
        mapname,
        ):
 
        # Load XModels JSON File
        
        # Load Model Properties
        #cmds.file(force=True)
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
 
        # Read XModels data
 
        for XModel in modeldata:
            # Load current XModel data from JSON
            #print(modelname)
            #print(XModel)
            if 'Name' in XModel:    
                try:
                    self.addXModel(xmodel_folder, XModel, 1, badModels)
                except:
                    return

 
            # Loading progress
            #SHEILAN_Tools.__log_info__(True, "loaded %i" % len(modeldata))
            print("loaded " + str(curAmount) + " of " + str(len(modeldata)))
            curAmount += 1
            #reporter = mel.eval('string $tmp = $gCommandReporter;')
            #cmds.cmdScrollFieldReporter(reporter, e=True, clear=True)
 
			
        # Delete all corrupted models
        for o in cmds.ls():
            if "|" not in o:
                if "Joints" in o or "LOD" in o:
                    cmds.delete(o)
				
        # Rescale mapGeo accordingly to match XModels' scale
 
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
 
        print('imported %i models' % (len(modeldata)-(len(badModels))))
        print('%i corruputed models' % len(badModels))
        print(badModels)

 
 
    def addXModel(self, xmodel_folder, XModel, duplicates, badModels):
        good_model = True
        modelname = XModel['Name']
        if "/" in modelname:
            modelname = modelname.split("/")[1]
        if "@" in modelname:
            mayamodel = modelname.replace("@","_")
        else:
            mayamodel = modelname
        xmodelPos = [XModel['PosX'],XModel['PosY'],XModel['PosZ']]
        xmodelRot = [XModel['RotX'],XModel['RotY'],XModel['RotZ']]
        try:
            # Check if model exists and duplicate, to avoid importing same model twice
            if cmds.objExists(mayamodel + '__%i' % duplicates) == True:
                # Go through duplicates untill there's an available name

                while cmds.objExists(mayamodel + '__%i'  % duplicates) == True:
                    duplicates += 1

                cmds.duplicate(mayamodel + '__%i' % (duplicates-1))

            else:

                # If current XModel doesn't exist in the scene, import it

                cmds.file(xmodel_folder + '\\' + modelname + '\\'
                            + modelname + '_LOD0.semodel', i=True)

                # Delete XModel's joints (who needs 'em, eh?)

                cmds.delete('Joints')

                # Rename model from modelname_LOD0 to modelname_DUPLICATENUMBER

                cmds.rename(modelname + '_LOD0', modelname + '__%i'
                            % duplicates)
                            
                # Parent mesh to group 'xmodels'

                cmds.parent(modelname + '__%i' % duplicates, 'xmodels')


        except:
            good_model = False
        
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

            cmds.scale(float(XModel['Scale']) * 0.5,
                        float(XModel['Scale']) * 0.5,
                        float(XModel['Scale']) * 0.5, currentModel,
                        absolute=True)

        if not good_model:
            badModels.append(modelname)