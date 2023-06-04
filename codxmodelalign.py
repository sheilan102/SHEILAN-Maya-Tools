#!/usr/bin/python
# -*- coding: utf-8 -*-
import maya.cmds as cmds
import pymel.core as pm
import logging
import SHEILAN_Tools
import maya.mel as mel

class XModelAlign(object):
 
    def __init__(self):

        self.product = ''
        # create our window
        
        self.win = cmds.window( 'Playermodel3', title="Load character", mnb=False, mxb=False, sizeable=False )
        
        self.layout = cmds.columnLayout(parent=self.win)

        # create projects option menu
        cmds.columnLayout(adj=True)
        cmds.text(label=' ', w=150)
        mode_game = cmds.optionMenu( "mode_game", l="Game", changeCommand=self.printNewMenuItem )
        cmds.menuItem( label='MW 1/2/3' )
        cmds.menuItem( label='BO 3/4' )
        #mode_rigged = cmds.checkBox("mode_rigged", l="Rigged")
        cmds.separator(h=15)
        cmds.button(label='Load fullbody model', w=100, h=30, command=lambda x: self.importModel())
        cmds.showWindow()

    def movePivot(self, object1, object2):
        position = pm.xform(object1, q=1, ws=1, rp=1)
        move_piv = pm.xform(object2,ws=1, rp=position,piv=position)
    def rigModel(self, file_path=""):
        rig_file = file_path.replace(".ma", "_BIND.mel").replace("\\","/")
        mel.eval('source "%s"' %(str(rig_file)))
    def loadModelData(self, file_path="", part="", count=0):
        # Load model
        try:
            cmds.file(file_path, i=True)

            # Data
            model_name = file_path.split("\\")[-1].split(".")[0]
            
            # Mapping
            cmds.rename(model_name, part + "_mesh" + str(count))
            cmds.rename("Joints", part + "_skeleton" + str(count))

        except:
            SHEILAN_Tools.__log_info__(False, "No model selected")
    def importModel(self):

        mode_game = cmds.optionMenu('mode_game', query=True, value=True)
        #mode_rigged = cmds.checkBox('mode_rigged', query=True, value=True)
        # Count characters in the scene
        playerbody_amount = self.nextModel()

        # Import body file
        body_file = SHEILAN_Tools.__importfile_dialog__(
            ".MA Files (*.ma)", "Load torso model", 1)
        defPart = None
        if "_torso" in body_file:
            defPart = "torso"
        elif "_body" in body_file:
            defPart = "body"
        if defPart != None:
            print("Wrong body part selected (please select body or torso model file)")
            head_file = body_file.replace(defPart,"head")

            # Load body
            self.loadModelData(body_file, "body", playerbody_amount)

            # Load & align head
            self.loadModelData(head_file, "head", playerbody_amount)  
            self.alignHead(playerbody_amount, mode_game)

            #Check if it's BO4 character
            if mode_game == "BO 3/4":
                # Import legs file
                legs_file = body_file.replace(defPart,"legs")
                # Import hands file
                arm_file = body_file.replace(defPart,"arms")
                
                # Delete Torso's hip joints
                cmds.delete("body_skeleton" + str(playerbody_amount) + "|j_mainroot|j_hip_le")
                cmds.delete("body_skeleton" + str(playerbody_amount) + "|j_mainroot|j_hip_ri") 

                # Load & align legs
                self.loadModelData(legs_file, "legs", playerbody_amount)
                self.alignLegs(playerbody_amount)

                # Load & align hands
                self.loadModelData(arm_file, "arms", playerbody_amount)
                self.alignHands(playerbody_amount)
        

                cmds.rename("body_skeleton" + str(playerbody_amount),'playermodel' + str(playerbody_amount) + '_skeleton')
                print("playercount " + str(playerbody_amount))

                self.rigModel(legs_file)
                self.rigModel(arm_file)
            
            self.rigModel(head_file)
            self.rigModel(body_file)
            # Delete color Sets
            for o in cmds.ls():
                if "WraithMesh" in o:
                    cmds.select(o)
                    if cmds.polyColorSet( query=True, allColorSets=True, representation=True ) != None:
                        cmds.polyColorSet( delete=True )
    def nextModel(self):
        count = 1
        while cmds.objExists('playermodel' + str(count) + '_skeleton'):
            count += 1
        
        return count
    def alignHead(self, playerbody_amount = 0, mode = ""):
        # Group head mesh + skeleton
        cmds.group(em=True, name='Head')
        cmds.parent("head_mesh" + str(playerbody_amount),"Head")
        cmds.parent("head_skeleton" + str(playerbody_amount),"Head")
        rotation = False

        if mode == "MW 1/2/3":
            head_joint_chain = "|j_spine4"
            body_joint_chain = "|tag_origin|j_mainroot|pelvis|torso_stabilizer|j_spinelower|back_low|j_spineupper|back_mid|j_spine4"
        elif mode == "BO 3/4":
            head_joint_chain = "|tag_origin|j_mainroot|j_spinelower|j_spineupper|j_spine4"
            body_joint_chain = "|j_mainroot|j_spinelower|j_spineupper|j_spine4"
            head_rotation = 90, 0, 80
            rotation = True
        # Allign head with body

        self.movePivot("head_skeleton" + str(playerbody_amount) + head_joint_chain,"Head")
        cmds.parentConstraint("body_skeleton" + str(playerbody_amount) + body_joint_chain , "Head")
        if rotation:
            cmds.rotate(head_rotation[0], head_rotation[1], head_rotation[2], "Head", absolute=True)
        cmds.delete("Head_parentConstraint1")
        
        # Attach Head to Torso
        try:
            cmds.delete("body_skeleton" + str(playerbody_amount) + body_joint_chain + "|j_neck")
        except:
            print("Body skeleton had no neck.")
        cmds.parent("head_skeleton" + str(playerbody_amount) + head_joint_chain + "|j_neck",
                    "body_skeleton" + str(playerbody_amount) + body_joint_chain)
        cmds.delete("Head|head_skeleton" + str(playerbody_amount))
        cmds.ungroup("Head")
    def alignHands(self, playerbody_amount):
        # Group hands mesh + skeleton
        cmds.group(em=True, name='Arms')
        cmds.parent("arms_mesh" + str(playerbody_amount),"Arms")
        cmds.parent("arms_skeleton" + str(playerbody_amount),"Arms")
        
        # Allign hands with body
        self.movePivot("arms_skeleton" + str(playerbody_amount) + "|tag_origin|j_mainroot|j_spinelower|j_spineupper|j_spine4|j_clavicle_le|j_shoulder_le","Arms")
        cmds.parentConstraint("body_skeleton" + str(playerbody_amount) + "|j_mainroot|j_spinelower|j_spineupper|j_spine4|j_clavicle_le|j_shoulder_le" , "Arms")
        cmds.rotate(90, 0, 90, "Arms", absolute=True)
        cmds.delete("Arms_parentConstraint1")
        
        # Attach Hands to Torso
        cmds.delete("body_skeleton" + str(playerbody_amount) + "|j_mainroot|j_spinelower|j_spineupper|j_spine4|j_clavicle_le")
        cmds.delete("body_skeleton" + str(playerbody_amount) + "|j_mainroot|j_spinelower|j_spineupper|j_spine4|j_clavicle_ri")
        cmds.parent("arms_skeleton" + str(playerbody_amount) + "|tag_origin|j_mainroot|j_spinelower|j_spineupper|j_spine4|j_clavicle_le",
                    "body_skeleton" + str(playerbody_amount) + "|j_mainroot|j_spinelower|j_spineupper|j_spine4")
        cmds.parent("arms_skeleton" + str(playerbody_amount) + "|tag_origin|j_mainroot|j_spinelower|j_spineupper|j_spine4|j_clavicle_ri",
                    "body_skeleton" + str(playerbody_amount) + "|j_mainroot|j_spinelower|j_spineupper|j_spine4")
        cmds.delete("Arms|arms_skeleton" + str(playerbody_amount))
        cmds.ungroup("Arms")
    def alignLegs(self, playerbody_amount):
        # Attach Leg joints to Torso
        legs_joints = cmds.listRelatives("legs_skeleton" + str(playerbody_amount) + "|j_mainroot",c=True)
        for joint in legs_joints:
            if joint == "j_spinelower":
                lowerSpine_joints = cmds.listRelatives("legs_skeleton" + str(playerbody_amount) + "|j_mainroot|" + joint,c=True)
                for ls_joint in lowerSpine_joints:
                    if ls_joint != "j_spineupper":
                        cmds.parent("legs_skeleton" + str(playerbody_amount) + "|j_mainroot|j_spinelower|" + ls_joint, "body_skeleton" + str(playerbody_amount) + "|j_mainroot|j_spinelower")
            else:
                cmds.parent("legs_skeleton" + str(playerbody_amount) + "|j_mainroot|" + joint, "body_skeleton" + str(playerbody_amount) + "|j_mainroot")
        
        cmds.delete("legs_skeleton" + str(playerbody_amount))
    def printNewMenuItem(self, item ):
        return item