"""A plugin designed to import and export SE formats from Autodesk Maya"""

import math
import json
import maya.mel as mel
import maya.cmds as cmds
import maya.OpenMayaMPx as OpenMayaMPx
import codimporter as CODImporter
import codxmodelalign as CODXModelAlign
import logging

def __first__(first_iter, second_iter):
    """Compare two iterable objects"""
    for elem in first_iter:
        if elem in second_iter:
            return first_iter
    return None

def __about_window__():
    """Present the about information"""
    cmds.confirmDialog(message="I like making shortcuts. Enjoy :)        \n\n- SHEILAN      ",
                       button=['OK'], defaultButton='OK', title="About")


def __remove_menu__():
    """Removes the plugin menu"""
    if cmds.control("SHEILANMenu", exists=True):
        cmds.deleteUI("SHEILANMenu", menu=True)
        
def __log_info__(type=True, format_str=""):
        logger = logging.getLogger("[SHEILAN]")
        logger.setLevel(logging.INFO)
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter('%(name)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        if type:
                logger.info(format_str)
        else:
                logger.warning(format_str)

def __create_menu__():
    """Creates the plugin menu"""
    __remove_menu__()

    # Create the base menu object
    cmds.setParent(mel.eval("$tmp = $gMainWindow"))
    menu = cmds.menu("SHEILANMenu", label="SHEILAN", tearOff=True)

    # COD menu controls
    cod_menu = cmds.menuItem(label="COD", subMenu=True)

    cmds.menuItem(label="Import COD Map",
                  annotation="Imports a COD map exported by Husky (SHEILAN's version)", command=lambda x: CODImporter.CODMAP())
    cmds.menuItem(label="Combine skeleton parts",
                  annotation="Combine all seperated body parts into one skeleton", command=lambda x: __align_xmodel__())

    cmds.setParent(cod_menu, menu=True)
    cmds.setParent(menu, menu=True)
    cmds.menuItem(divider=True)

    # Reload and about controls
    cmds.menuItem(label="About", command=lambda x: __about_window__())
def __align_xmodel__():
        try:
                CODXModelAlign.XModelAlign()
        except:
                print"lul"
                __log_info__(False, "No playermodels in the scene")
        
def initializePlugin(m_object):
    """Register the plugin"""
    m_plugin = OpenMayaMPx.MFnPlugin(m_object, "SHEILAN", "1.0", "Any")
    __create_menu__()


def uninitializePlugin(m_object):
    """Unregister the plugin"""
    m_plugin = OpenMayaMPx.MFnPlugin(m_object)
    __remove_menu__()
