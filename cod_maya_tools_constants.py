# -*- coding: utf-8 -*-
"""
Centralized constants for SHEILAN Maya Tools.

This file stores common strings, paths, and numerical values used across
the plugin modules to facilitate easier updates and maintain consistency.
"""

# --- Logging Constants ---
DEFAULT_LOGGER_NAME = "SHEILAN_Plugin"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# --- General Maya & Plugin Constants ---
MENU_NAME = "SHEILAN_COD_Tools_Menu"
MENU_LABEL = "SHEILAN COD Tools"
COD_SUBMENU_LABEL = "COD Importers"

# About Window
ABOUT_TITLE = "About SHEILAN Maya Tools"
ABOUT_MESSAGE = ("SHEILAN Maya Tools\n\n"
                 "A collection of tools for importing Call of Duty assets into Maya.\n"
                 "Developed by SHEILAN.\n\n"
                 "Version: 1.2.0") # Updated version example

# Menu Item Labels
IMPORT_COD_MAP_LABEL = "Import COD Map..."
IMPORT_COD_MAP_UNAVAILABLE_LABEL = "Import COD Map (CODImporter not found)"
IMPORT_FULLBODY_CHAR_LABEL = "Import Full Body Character (XModelAlign)..."
IMPORT_FULLBODY_CHAR_UNAVAILABLE_LABEL = "Import Full Body Character (CODXModelAlign not found)"
ABOUT_LABEL = "About SHEILAN Tools"

PLUGIN_VERSION = "1.2.0" # General plugin version, updated
VENDOR_NAME = "SHEILAN"

# --- Numerical Constants ---
INCHES_TO_CM = 0.3937007874015748
DEFAULT_MODEL_SCALE = 0.01  # For final map/model scaling

# --- File Naming, Suffixes & Prefixes ---
XMODEL_PROPERTIES_SUFFIX = "_xmodels.json"
MAP_GEOMETRY_SUFFIX = ".obj"
BAD_MODELS_LOG_SUFFIX = "_badModels.txt"
XMODEL_LOD0_SUFFIX = "_LOD0.ma"
RIG_SCRIPT_SUFFIX = "_BIND.mel"

# --- Maya Object Naming Conventions ---
# Groups
XMODELS_GROUP = "xmodels"
MAP_GEOMETRY_GROUP = "mapGeometry"

# Common Object Names
JOINTS_OBJECT_NAME = "Joints"
LOD_OBJECT_NAME_PART = "LOD" # Partial string to identify Level Of Detail objects

# Character/Player Model Specific Naming
PLAYER_MODEL_PREFIX = "playermodel"
MESH_SUFFIX = "_mesh"
SKELETON_SUFFIX = "_skeleton"

# --- Character Importer (XModelAlign) Specific Constants ---
# Window
CHAR_ALIGN_WINDOW_TITLE = "Load Character"
CHAR_ALIGN_WINDOW_NAME = "PlayerModelAlignWindow"

# UI Elements
GAME_MODE_OPTIONMENU = "mode_game_om"

# Game Modes (as strings for UI and logic)
GAME_MODE_MW = "MW 1/2/3" # Modern Warfare series (original trilogy)
GAME_MODE_BO = "BO 3/4"   # Black Ops 3/4 series

# Character Parts (suffixes or identifiers used in filenames)
PART_TORSO = "_torso"
PART_BODY = "_body"
PART_HEAD = "_head"
PART_LEGS = "_legs"
PART_ARMS = "_arms"

# Alignment Groups (temporary groups used during alignment process)
HEAD_ALIGN_GROUP = "Head_align_grp"
ARMS_ALIGN_GROUP = "Arms_align_grp"

# Specific Identifiers
WRAITHMESH_IDENTIFIER = "WraithMesh" # Used to identify meshes for color set deletion

# --- Joint Naming and Paths ---
# Common joint names or path components. Full paths are often constructed using these.
TAG_ORIGIN = "tag_origin"

JOINT_MAIN_ROOT = "j_mainroot"
JOINT_PELVIS = "pelvis"
JOINT_TORSO_STABILIZER = "torso_stabilizer" # Example, may vary in specific rigs
JOINT_SPINE_LOWER = "j_spinelower"
JOINT_SPINE_UPPER = "j_spineupper"
JOINT_SPINE_4 = "j_spine4"
JOINT_NECK = "j_neck"
JOINT_CLAVICLE_LE = "j_clavicle_le"
JOINT_CLAVICLE_RI = "j_clavicle_ri"
JOINT_SHOULDER_LE = "j_shoulder_le"
JOINT_HIP_LE = "j_hip_le"
JOINT_HIP_RI = "j_hip_ri"

# Pre-constructed example joint chain paths for specific game modes/rigs.
# These illustrate how base joint names can form parts of longer paths.
# Note: "back_low" and "back_mid" are examples of rig-specific intermediate joints.
MW_BODY_JOINT_CHAIN_FOR_HEAD = (f"|{TAG_ORIGIN}|{JOINT_MAIN_ROOT}|{JOINT_PELVIS}|"
                                f"{JOINT_TORSO_STABILIZER}|{JOINT_SPINE_LOWER}|back_low|"
                                f"{JOINT_SPINE_UPPER}|back_mid|{JOINT_SPINE_4}")

BO_BODY_JOINT_CHAIN_FOR_HEAD = (f"|{JOINT_MAIN_ROOT}|{JOINT_SPINE_LOWER}|"
                                f"{JOINT_SPINE_UPPER}|{JOINT_SPINE_4}")

BO_ARM_PIVOT_JOINT_REL = (f"|{TAG_ORIGIN}|{JOINT_MAIN_ROOT}|{JOINT_SPINE_LOWER}|"
                          f"{JOINT_SPINE_UPPER}|{JOINT_SPINE_4}|{JOINT_CLAVICLE_LE}|"
                          f"{JOINT_SHOULDER_LE}")

BO_BODY_TARGET_FOR_ARM_REL = (f"|{JOINT_MAIN_ROOT}|{JOINT_SPINE_LOWER}|{JOINT_SPINE_UPPER}|"
                              f"{JOINT_SPINE_4}|{JOINT_CLAVICLE_LE}|{JOINT_SHOULDER_LE}")

BO_BODY_CLAVICLE_PARENT = (f"|{JOINT_MAIN_ROOT}|{JOINT_SPINE_LOWER}|{JOINT_SPINE_UPPER}|"
                           f"{JOINT_SPINE_4}")

# Corrected typo from TAG_origin to TAG_ORIGIN
BO_ARM_CLAVICLE_LE_REL = (f"|{TAG_ORIGIN}|{JOINT_MAIN_ROOT}|{JOINT_SPINE_LOWER}|"
                          f"{JOINT_SPINE_UPPER}|{JOINT_SPINE_4}|{JOINT_CLAVICLE_LE}")

BO_ARM_CLAVICLE_RI_REL = (f"|{TAG_ORIGIN}|{JOINT_MAIN_ROOT}|{JOINT_SPINE_LOWER}|"
                          f"{JOINT_SPINE_UPPER}|{JOINT_SPINE_4}|{JOINT_CLAVICLE_RI}")


# --- Rotations (as tuples in degrees: X, Y, Z) ---
HEAD_ROTATION_BO = (90.0, 0.0, 80.0)
ARMS_ROTATION_BO = (90.0, 0.0, 90.0)

# --- File Dialog Filters ---
MAYA_FILES_FILTER = "Maya Files (*.ma *.mb)"
ALL_FILES_FILTER = "All Files (*.*)"

# Note: Some constants, especially complex joint paths, might still need
# to be constructed dynamically in the code if they vary too much.
# These constants aim to cover the most common and stable parts.
