#!/usr/bin/python
# -*- coding: utf-8 -*-
from functools import partial
import os
import os.path
import maya.cmds as cmds
import json
import maya.mel as mel
import logging
import SHEILAN_Tools

class CODMAP(object):
 
    def __init__(self):
        self.product = ''
        map_dest = self.__importfile_dialog__(
            "MAP Folder", "Locate MAP directory", 3)
        xmodel_folder = self.__importfile_dialog__(
            "XModel Folder", "Locate Greyhound's XModel directory", 3)
        if map_dest and xmodel_folder:
            map_name = map_dest.split("\\")
            map_name = map_name[len(map_name)-1]
            map_dest = map_dest + "\\" + map_name
            print(map_dest)
            print(xmodel_folder)
            print(map_name)
            try:
                self.importMap(map_dest,xmodel_folder,map_name)
                SHEILAN_Tools.__log_info__(True, "Map imported succesfully")
            except:
                SHEILAN_Tools.__log_info__(False, "Wrong directory selected")
        else:
            SHEILAN_Tools.__log_info__(False, "One or two of the necessary directories were not selected")

    def __importfile_dialog__(self, filter_str="", caption_str="", lul=1):
        """Ask the user for an input file"""
        if cmds.about(version=True)[:4] == "2012":
            import_from = cmds.fileDialog2(
                fileMode=lul, fileFilter=filter_str, caption=caption_str)
        else:
            import_from = cmds.fileDialog2(fileMode=lul,
                                        dialogStyle=2,
                                        fileFilter=filter_str,
                                        caption=caption_str)
        if not import_from or import_from[0].strip() == "":
            return None

        path = import_from[0].strip()
        path_split = os.path.splitext(path)
        if path_split[1] == ".*":
            path = path_split

        return path.replace("/", "\\")


    def importMap(
        self,
        map_dest,
        xmodel_folder,
        mapname,
        ):
 
        # Load XModels JSON File
 
        
        # Load Model Properties
        #cmds.file(force=True)
        json_models = open(map_dest + ".json") 
        modeldata = json.load(json_models)
 
        # Model Count
 
        curAmount = 1
        errors = 0
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
 
        for XModel in modeldata['XModels']:
 
            # duplicates counter
 
            duplicates = 1
 
            # Load current XModel data from JSON
			model_details = modeldata['XModels'][XModel]
            modelname = model_details['Name']
			try:
				self.addXModel(xmodel_folder, XModel, modeldata, 1)
			except:
				if not any(modelname in s for s in some_list):
					badModels.append(modelname)
 
            # Loading progress
            #SHEILAN_Tools.__log_info__(True, 'loaded ' + str(curAmount) + ' of ' + str(len(modeldata['XModels'])))
			print("loaded " + str(curAmount) + " of " + str(len(modeldata['XModels'])))
			
            curAmount += 1
 
            # If a corrupted model is loaded, it still adds a blank mesh, so we gotta delete it
 
            #if cmds.objExists(modelname + '_LOD0') == True:
            #    cmds.delete(modelname + '_LOD0')
            #    cmds.delete('Joints')
 
            reporter = mel.eval('string $tmp = $gCommandReporter;')
            cmds.cmdScrollFieldReporter(reporter, e=True, clear=True)
 
	# Print corrupted model names
        for b in badModels:
		print b
			
        # Delete all corrupted models
        for o in cmds.ls:
		if "LOD" in o or "Joints"  in o:
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
 
        print 'imported %i models' % curAmount
        print '%i corruputed models' % errors
        
		#for b in badModels:
        #    print b
 
 
    def addXModel(self, xmodel_folder, XModel, data, duplicates):
        good_model = True
        xmodelData = data['XModels'][XModel]
        modelname = xmodelData['Name']
        if "/" in modelname:
            modelname = modelname.split("/")[1]
        if "@" in modelname:
            mayamodel = modelname.replace("@","_")
        else:
            mayamodel = modelname
        xmodelPos = [xmodelData['PosX'],xmodelData['PosY'],xmodelData['PosZ']]
        xmodelRot = [xmodelData['RotX'],xmodelData['RotY'],xmodelData['RotZ']]
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

            cmds.scale(float(xmodelData['Scale']) * 0.5,
                        float(xmodelData['Scale']) * 0.5,
                        float(xmodelData['Scale']) * 0.5, currentModel,
                        absolute=True)
        
