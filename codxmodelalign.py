#!/usr/bin/python
# -*- coding: utf-8 -*-
import maya.cmds as cmds
import pymel.core as pm
import logging

class XModelAlign(object):
 
    def __init__(self):
        self.product = ''
        # Delete Torso's hip joints
        cmds.delete("body_skeleton|j_mainroot|j_hip_le")
        cmds.delete("body_skeleton|j_mainroot|j_hip_ri")
        
        # Attach Leg joints to Torso
        cmds.parent("legs_skeleton|j_mainroot|j_hip_ri", "body_skeleton|j_mainroot")
        cmds.parent("legs_skeleton|j_mainroot|j_hip_le", "body_skeleton|j_mainroot")
        cmds.delete("legs_skeleton")
        
        # Group hands mesh + skeleton
        cmds.group(em=True, name='Arms')
        cmds.parent("arms_mesh","Arms")
        cmds.parent("arms_skeleton","Arms")
        
        # Allign hands with body
        self.movePivot("arms_skeleton|tag_origin|j_mainroot|j_spinelower|j_spineupper|j_spine4|j_clavicle_le|j_shoulder_le","Arms")
        cmds.parentConstraint("body_skeleton|j_mainroot|j_spinelower|j_spineupper|j_spine4|j_clavicle_le|j_shoulder_le" , "Arms")
        cmds.rotate(90, 0, 90, "Arms", absolute=True)
        cmds.delete("Arms_parentConstraint1")
        
        # Attach Hands to Torso
        cmds.delete("body_skeleton|j_mainroot|j_spinelower|j_spineupper|j_spine4|j_clavicle_le")
        cmds.delete("body_skeleton|j_mainroot|j_spinelower|j_spineupper|j_spine4|j_clavicle_ri")
        cmds.parent("arms_skeleton|tag_origin|j_mainroot|j_spinelower|j_spineupper|j_spine4|j_clavicle_le",
                    "body_skeleton|j_mainroot|j_spinelower|j_spineupper|j_spine4")
        cmds.parent("arms_skeleton|tag_origin|j_mainroot|j_spinelower|j_spineupper|j_spine4|j_clavicle_ri",
                    "body_skeleton|j_mainroot|j_spinelower|j_spineupper|j_spine4")
        cmds.delete("Arms|arms_skeleton")
        cmds.ungroup("Arms")
        
        # Group head mesh + skeleton
        cmds.group(em=True, name='Head')
        cmds.parent("head_mesh","Head")
        cmds.parent("head_skeleton","Head")
        
        # Allign head with body
        self.movePivot("tag_origin|j_mainroot|j_spinelower|j_spineupper|j_spine4","Head")
        cmds.parentConstraint("body_skeleton|j_mainroot|j_spinelower|j_spineupper|j_spine4" , "Head")
        cmds.rotate(90, 0, 80, "Head", absolute=True)
        cmds.delete("Head_parentConstraint1")
        
        # Attach Head to Torso
        try:
            cmds.delete("body_skeleton|j_mainroot|j_spinelower|j_spineupper|j_spine4|j_neck")
        except:
            print"Body skeleton had no neck."
        cmds.parent("head_skeleton|tag_origin|j_mainroot|j_spinelower|j_spineupper|j_spine4|j_neck",
                    "body_skeleton|j_mainroot|j_spinelower|j_spineupper|j_spine4")
        cmds.delete("Head|head_skeleton")
        cmds.ungroup("Head")
        
        
        cmds.rename("body_skeleton","fullbody_skeleton")

    def movePivot(self, object1, object2):
        position = pm.xform(object1, q=1, ws=1, rp=1)
        move_piv = pm.xform(object2,ws=1, rp=position,piv=position)
    
