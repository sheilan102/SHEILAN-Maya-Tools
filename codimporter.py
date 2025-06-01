# -*- coding: utf-8 -*-
"""
COD Map Importer for Maya.

This module provides the CODMAP class, which facilitates the import of
Call of Duty map data, including map geometry and XModels, into the Maya scene.
It handles path selection, JSON parsing for XModel definitions, Maya scene setup,
geometry and XModel import, and final scene adjustments.
"""
import json
import os

import maya.cmds as cmds
import maya.mel as mel # Retained for potential future use or if called by other scripts.

import cod_maya_tools_constants as consts
import SHEILAN_Tools

LOG = SHEILAN_Tools.get_logger(__name__)


class CODMAP(object):
    """
    Imports Call of Duty map data, including map geometry and XModels, into Maya.

    The process involves:
    1. Prompting the user for map and XModel directories.
    2. Loading XModel definitions from a JSON file.
    3. Setting up necessary groups in the Maya scene.
    4. Importing the main map geometry (.obj).
    5. Processing and placing each XModel based on the definitions.
    6. Finalizing the scene with scaling and cleanup.
    """

    def __init__(self):
        """
        Initializes the CODMAP importer.

        Prompts the user for necessary folder paths using SHEILAN_Tools.import_file_dialog,
        stores them as instance variables, and if paths are valid, automatically
        triggers the main import process by calling `_perform_import()`.
        """
        self.map_dest_folder = None
        self.xmodel_folder = None
        self.map_name = None
        self.map_file_base = None  # Full path to map file, typically folder_path/map_name

        LOG.info("CODMAP importer initialized. Requesting folder paths...")
        map_dest_folder_raw = SHEILAN_Tools.import_file_dialog(
            caption="Select MAP Source Folder",
            file_mode=3, # Directory mode
            filter_str="Folders" # Example filter, adjust if needed
        )
        xmodel_folder_raw = SHEILAN_Tools.import_file_dialog(
            caption="Select XModel Root Folder",
            file_mode=3, # Directory mode
            filter_str="Folders"
        )

        if map_dest_folder_raw and xmodel_folder_raw:
            self.map_dest_folder = os.path.normpath(map_dest_folder_raw)
            self.xmodel_folder = os.path.normpath(xmodel_folder_raw)

            # Assuming the selected folder's name is the map name
            self.map_name = os.path.basename(self.map_dest_folder)
            self.map_file_base = os.path.join(self.map_dest_folder, self.map_name)

            LOG.info(f"MAP file base determined as: {self.map_file_base}")
            LOG.info(f"XModel folder set to: {self.xmodel_folder}")
            LOG.info(f"Map name derived as: {self.map_name}")

            self._perform_import()
        else:
            LOG.error("Initialization failed: MAP source folder or XModel root folder was not selected.")

    def _load_xmodel_definitions(self, json_path):
        """
        Loads XModel definitions from the provided JSON file path.

        Args:
            json_path (str): Full path to the _xmodels.json file.

        Returns:
            list or None: A list of XModel data dictionaries if successful,
                          None otherwise.
        """
        LOG.debug(f"Attempting to load XModel definitions from: {json_path}")
        try:
            with open(json_path, 'r', encoding='utf-8') as json_file:
                model_data = json.load(json_file)
            LOG.info(f"Successfully loaded {len(model_data)} XModel definitions from '{json_path}'.")
            return model_data
        except FileNotFoundError:
            LOG.error(f"XModel JSON file not found: {json_path}.")
            return None
        except json.JSONDecodeError as e:
            LOG.error(f"Error decoding JSON from file '{json_path}': {e}.")
            return None
        except Exception as e:
            LOG.error(f"An unexpected error occurred while loading '{json_path}': {e}", exc_info=True)
            return None

    def _setup_scene_groups(self):
        """
        Creates standard top-level groups in Maya for organizing imported assets.

        Returns:
            dict or None: A dictionary with keys 'xmodels', 'map_overall', 'map_geometry'
                          mapping to their respective group names if successful.
                          Returns None if `self.map_name` is not set.
        """
        if not self.map_name:
            LOG.error("Cannot setup scene groups: instance variable 'map_name' is not initialized.")
            return None

        LOG.debug("Setting up scene groups...")
        xmodels_grp = consts.XMODELS_GROUP
        map_overall_grp = f'{self.map_name}_group' # Main group for this specific map
        map_geo_grp = consts.MAP_GEOMETRY_GROUP

        # Ensure groups are unique or handle existing ones if necessary
        # For now, creating them directly.
        cmds.group(em=True, name=xmodels_grp, world=True) # Ensure top-level
        cmds.group(em=True, name=map_overall_grp, world=True)
        cmds.group(em=True, name=map_geo_grp, world=True)
        LOG.info(f"Created scene groups: '{xmodels_grp}', '{map_overall_grp}', '{map_geo_grp}'.")

        return {
            'xmodels': xmodels_grp,
            'map_overall': map_overall_grp,
            'map_geometry': map_geo_grp
        }

    def _import_map_geometry(self, map_obj_path, map_geometry_group_name):
        """
        Imports the main map geometry from an .obj file and parents its components.

        Args:
            map_obj_path (str): Full path to the map's .obj file.
            map_geometry_group_name (str): Name of the Maya group to parent the geometry to.
        """
        LOG.debug(f"Importing map geometry from: {map_obj_path}")
        if not os.path.exists(map_obj_path):
            LOG.error(f"Map OBJ file not found: '{map_obj_path}'. Skipping map geometry import.")
            return

        try:
            imported_geo_nodes = cmds.file(map_obj_path, i=True, type="OBJ",
                                           options="mo=1", # Merge objects option
                                           returnNewNodes=True)
            LOG.info(f"Successfully imported map geometry from '{map_obj_path}'.")

            if imported_geo_nodes:
                for node in imported_geo_nodes:
                    # Only parent actual transform nodes created by the importer
                    if cmds.nodeType(node) == 'transform':
                        try:
                            cmds.parent(node, map_geometry_group_name)
                        except RuntimeError as e:
                            LOG.warning(f"Could not parent imported geometry node '{node}' "
                                        f"to group '{map_geometry_group_name}': {e}")
            else:
                # Fallback: If `returnNewNodes` is empty or unreliable, try to parent
                # existing unparented geometry. This is less precise.
                LOG.debug("`cmds.file` returned no nodes. Attempting fallback geometry parenting.")
                all_scene_geometry_shapes = cmds.ls(geometry=True, long=True)
                if all_scene_geometry_shapes:
                    all_scene_transforms = cmds.listRelatives(all_scene_geometry_shapes, parent=True, fullPath=True) or []
                    # Parent unique transforms that are not already correctly parented
                    for geo_transform in set(all_scene_transforms):
                        current_parent_list = cmds.listRelatives(geo_transform, parent=True, fullPath=True)
                        current_parent = current_parent_list[0] if current_parent_list else None

                        # Avoid re-parenting if already in the target group or part of XModels
                        if current_parent != map_geometry_group_name and \
                           (not current_parent or consts.XMODELS_GROUP not in current_parent):
                            try:
                                cmds.parent(geo_transform, map_geometry_group_name)
                            except RuntimeError as e:
                                 LOG.warning(f"Fallback: Could not parent scene geometry '{geo_transform}' "
                                             f"to '{map_geometry_group_name}': {e}")
        except RuntimeError as e:
            LOG.error(f"Runtime error during map OBJ import from '{map_obj_path}': {e}", exc_info=True)
        except Exception as e:
            LOG.error(f"Unexpected error during map geometry import from '{map_obj_path}': {e}", exc_info=True)

    def _process_xmodels(self, model_data, bad_models_list):
        """
        Iterates through XModel definitions and calls `_add_xmodel_to_scene` for each.

        Args:
            model_data (list): List of XModel data dictionaries from the JSON file.
            bad_models_list (list): A list (passed by reference) to append details
                                    of XModels that failed to import or process.
        """
        if not model_data:
            LOG.warning("No XModel data provided to _process_xmodels. Skipping XModel processing.")
            return
        if self.xmodel_folder is None:
            LOG.error("'xmodel_folder' is not set. Cannot process XModels.")
            return

        num_models = len(model_data)
        LOG.info(f"Starting processing of {num_models} XModels...")
        for i, xmodel_data_item in enumerate(model_data):
            log_prefix = f"[XModel {i + 1}/{num_models}]"
            if 'Name' in xmodel_data_item:
                LOG.debug(f"{log_prefix} Processing XModel: {xmodel_data_item['Name']}")
                self._add_xmodel_to_scene(self.xmodel_folder, xmodel_data_item, 1, bad_models_list)
            else:
                LOG.warning(f"{log_prefix} Skipping XModel data item at index {i} due to missing 'Name' field.")
            # Removed per-model "Processed X of Y" log to reduce verbosity; overall progress is logged by caller.

    def _finalize_scene(self, scene_groups, bad_models_list):
        """
        Performs final scene operations: writes bad models log, cleans up remnants,
        scales geometry, parents groups, and logs summary statistics.

        Args:
            scene_groups (dict): Dictionary with names of 'xmodels', 'map_overall',
                                 and 'map_geometry' groups.
            bad_models_list (list): List of (model_name, error_message) tuples for failed XModels.
        """
        if not self.map_file_base or not scene_groups:
            LOG.error("Cannot finalize scene: 'map_file_base' or 'scene_groups' are not initialized.")
            return

        LOG.info("Finalizing imported map scene...")
        map_overall_group = scene_groups['map_overall']
        map_geometry_group = scene_groups['map_geometry']
        xmodels_group = scene_groups['xmodels']

        bad_models_file_path = f"{self.map_file_base}{consts.BAD_MODELS_LOG_SUFFIX}"
        try:
            with open(bad_models_file_path, "w", encoding='utf-8') as f_badmodels:
                for model_name, error_msg in bad_models_list:
                    f_badmodels.write(f"Model: {model_name}, Error: {error_msg}\n")
            LOG.info(f"Bad models log written to: '{bad_models_file_path}'")
        except IOError as e:
            LOG.error(f"Could not write bad models log to '{bad_models_file_path}': {e}", exc_info=True)

        LOG.debug("Deleting remnant top-level 'Joints' and 'LOD' objects...")
        for obj_name in cmds.ls(assemblies=True): # Consider only top-level objects
            if (consts.JOINTS_OBJECT_NAME in obj_name or consts.LOD_OBJECT_NAME_PART in obj_name) and \
               obj_name not in scene_groups.values(): # Avoid deleting our main groups
                try:
                    cmds.delete(obj_name)
                    LOG.debug(f"Deleted remnant top-level object: '{obj_name}'")
                except RuntimeError as e:
                    LOG.warning(f"Could not delete remnant object '{obj_name}': {e}")

        LOG.debug(f"Scaling map geometry group '{map_geometry_group}' by {consts.INCHES_TO_CM}.")
        if cmds.objExists(map_geometry_group):
            cmds.scale(consts.INCHES_TO_CM, consts.INCHES_TO_CM, consts.INCHES_TO_CM,
                       map_geometry_group, absolute=True)

        LOG.debug(f"Parenting main groups to '{map_overall_group}'.")
        try:
            if cmds.objExists(xmodels_group) and cmds.objExists(map_overall_group):
                if (cmds.listRelatives(xmodels_group, parent=True) or [None])[0] != map_overall_group:
                    cmds.parent(xmodels_group, map_overall_group)
            if cmds.objExists(map_geometry_group) and cmds.objExists(map_overall_group):
                 if (cmds.listRelatives(map_geometry_group, parent=True) or [None])[0] != map_overall_group:
                    cmds.parent(map_geometry_group, map_overall_group)
        except RuntimeError as e:
            LOG.error(f"Error parenting main groups into '{map_overall_group}': {e}", exc_info=True)

        try:
            all_poly_meshes = cmds.ls(type='mesh', long=True)
            if all_poly_meshes:
                LOG.debug("Checking for 'colorSet1' on polygon meshes for potential deletion.")
                # This operation can be slow. For now, it's included.
                # Consider making this optional if performance is an issue on large scenes.
                # Only delete if 'colorSet1' exists and is the current color set on some meshes.
                # This avoids errors if the set doesn't exist or isn't active.
                if 'colorSet1' in (cmds.polyColorSet(all_poly_meshes, q=True, allColorSets=True) or []):
                    if any(c == 'colorSet1' for c in (cmds.polyColorSet(all_poly_meshes, q=True, currentColorSet=True) or []) if c):
                        cmds.polyColorSet(delete=True, colorSet='colorSet1')
                        LOG.info("Attempted to delete 'colorSet1' from applicable meshes.")
        except Exception as e: # Broad exception as polyColorSet can be tricky
            LOG.warning(f"Could not query or delete 'colorSet1': {e}", exc_info=True)

        LOG.debug(f"Applying final scene scale of {consts.DEFAULT_MODEL_SCALE} to '{map_overall_group}'.")
        if cmds.objExists(map_overall_group):
            cmds.scale(consts.DEFAULT_MODEL_SCALE, consts.DEFAULT_MODEL_SCALE, consts.DEFAULT_MODEL_SCALE,
                       map_overall_group, absolute=True)

        # Log summary statistics
        # Re-loading definitions for count might be slow; consider passing total from _perform_import
        json_model_defs_path = f"{self.map_file_base}{consts.XMODEL_PROPERTIES_SUFFIX}"
        model_data_for_count = self._load_xmodel_definitions(json_model_defs_path)
        num_total_models = len(model_data_for_count) if model_data_for_count else 0

        num_bad_models = len(bad_models_list)
        num_good_models = num_total_models - num_bad_models
        LOG.info(f"Map import finalized. Imported {num_good_models} of {num_total_models} XModels successfully.")
        if num_bad_models > 0:
            LOG.info(f"{num_bad_models} XModels were problematic. See '{bad_models_file_path}' for details.")

    def _perform_import(self):
        """
        Main private method orchestrating the entire map import process:
        Loads definitions, sets up groups, imports geometry, processes XModels, and finalizes.
        """
        if not all([self.map_file_base, self.xmodel_folder, self.map_name]):
            LOG.critical("Import cannot be performed: Essential path or map name information is missing from instance.")
            return

        LOG.info(f"Starting full import process for map: {self.map_name}")

        model_data = self._load_xmodel_definitions(f"{self.map_file_base}{consts.XMODEL_PROPERTIES_SUFFIX}")
        if model_data is None: # Explicitly check for None, as empty list is valid (no models)
            LOG.error("Failed to load XModel definitions. Aborting import.")
            return

        scene_groups = self._setup_scene_groups()
        if not scene_groups: # Check if dictionary is None or empty
            LOG.error("Failed to set up scene groups. Aborting import.")
            return

        self._import_map_geometry(
            f"{self.map_file_base}{consts.MAP_GEOMETRY_SUFFIX}",
            scene_groups['map_geometry']
        )

        bad_models_list = []
        self._process_xmodels(model_data, bad_models_list) # bad_models_list is populated here

        self._finalize_scene(scene_groups, bad_models_list)
        LOG.info(f"Full import process for map '{self.map_name}' has finished.")

    def _find_unique_maya_name(self, base_name, initial_suffix_count=1):
        """
        Finds a unique Maya object name by appending a numerical suffix if necessary.
        Example: base_name -> base_name__1, base_name__2, etc.

        Args:
            base_name (str): The desired base name for the object.
            initial_suffix_count (int): Starting number for the suffix. Typically 1.

        Returns:
            tuple: (str: unique_name, int: final_suffix_count used for uniqueness)
        """
        current_count = initial_suffix_count
        # If initial_suffix_count is 1 and base_name is free, use base_name without suffix.
        if current_count == 1 and not cmds.objExists(base_name):
            return base_name, current_count

        # Otherwise, always use suffix, starting count might be > 1 or base_name was taken.
        final_name = f"{base_name}__{current_count}"
        while cmds.objExists(final_name):
            current_count += 1
            final_name = f"{base_name}__{current_count}"
        return final_name, current_count

    def _maybe_duplicate_existing(self, maya_object_base_name, target_unique_name, current_instance_suffix):
        """
        Attempts to duplicate an existing Maya object if this instance is a subsequent one.
        Checks for `basename__N-1` or `basename` (if `current_instance_suffix` is 2).

        Args:
            maya_object_base_name (str): The base name of the XModel (e.g., "prop_car").
            target_unique_name (str): The target unique name for this instance (e.g., "prop_car__2").
            current_instance_suffix (int): The suffix number for this instance (e.g., 2 for "__2").

        Returns:
            bool: True if duplication occurred successfully.

        Raises:
            RuntimeError: If Maya's `cmds.duplicate` fails.
        """
        source_for_duplication = None
        if current_instance_suffix > 1:
            # Try to duplicate "basename__N-1"
            prev_suffixed_name = f"{maya_object_base_name}__{current_instance_suffix - 1}"
            if cmds.objExists(prev_suffixed_name):
                source_for_duplication = prev_suffixed_name
            # If current_instance_suffix is 2, also check if "basename" (no suffix) exists
            elif current_instance_suffix == 2 and cmds.objExists(maya_object_base_name):
                source_for_duplication = maya_object_base_name

        if source_for_duplication:
            LOG.debug(f"Attempting to duplicate '{source_for_duplication}' to create '{target_unique_name}'.")
            try:
                cmds.duplicate(source_for_duplication, name=target_unique_name)
                LOG.info(f"Successfully duplicated '{source_for_duplication}' to '{target_unique_name}'.")
                return True
            except RuntimeError as e: # Maya command error
                LOG.error(f"RuntimeError duplicating model '{source_for_duplication}' to '{target_unique_name}': {e}")
                raise # Re-raise to be caught by _add_xmodel_to_scene
        return False

    def _import_new_xmodel(self, model_file_path, target_maya_name, xmodel_name_from_json):
        """
        Imports an XModel from its .ma file, renames its root, and parents it.

        Args:
            model_file_path (str): Full path to the XModel's .ma file.
            target_maya_name (str): The unique name to give the imported model's root in Maya.
            xmodel_name_from_json (str): Original name from XModel JSON data (for logging and matching).

        Returns:
            bool: True if import and setup were successful.

        Raises:
            ValueError: If the model file is not found, or if a suitable root node cannot be identified.
            RuntimeError: If Maya commands (file import, rename, parent) fail.
        """
        if not os.path.exists(model_file_path):
            raise ValueError(f"XModel file not found: {model_file_path}")

        LOG.debug(f"Importing new XModel from: {model_file_path}")
        imported_nodes = cmds.file(model_file_path, i=True, returnNewNodes=True, defaultNamespace=True)
        if not imported_nodes:
            LOG.warning(f"No nodes returned by Maya after importing '{model_file_path}'. Check file content.")
            # This could be an empty file or an issue with the importer.
            raise ValueError(f"Import of '{model_file_path}' yielded no nodes.")

        # Heuristic to find the main root node of the imported model
        model_base_filename = os.path.basename(xmodel_name_from_json)
        expected_root_lod = f"{model_base_filename}{consts.LOD_OBJECT_NAME_PART}0"
        expected_root_simple = model_base_filename

        actual_root_node = None
        potential_roots = [n for n in imported_nodes if cmds.nodeType(n) == 'transform' and not cmds.listRelatives(n, parent=True, fullPath=True)]

        if not potential_roots: # Fallback if no top-level transforms in direct import list
             potential_roots = [n for n in cmds.ls(imported_nodes, type='transform', long=True) if not cmds.listRelatives(n, parent=True, fullPath=True)]

        for r_node in potential_roots:
            node_name_no_ns = r_node.split(':')[-1]
            if node_name_no_ns == expected_root_lod or node_name_no_ns == expected_root_simple:
                actual_root_node = r_node
                break

        if not actual_root_node and potential_roots:
            actual_root_node = potential_roots[0]
            LOG.warning(f"Could not find expected root for '{xmodel_name_from_json}'. Using first potential root: '{actual_root_node}'.")

        if not actual_root_node:
            raise ValueError(f"No suitable root node identified for XModel '{xmodel_name_from_json}' from '{model_file_path}'. Imported nodes: {imported_nodes}")

        # Delete joints from the imported model part
        child_joints = cmds.listRelatives(actual_root_node, allDescendents=True, type="joint", fullPath=True)
        if child_joints:
            try:
                cmds.delete(child_joints)
                LOG.debug(f"Deleted joints under '{actual_root_node}' for XModel '{target_maya_name}'.")
            except RuntimeError as e: # Log if deletion fails but proceed with model.
                LOG.warning(f"Could not delete joints under '{actual_root_node}': {e}")

        cmds.rename(actual_root_node, target_maya_name)
        LOG.debug(f"Renamed XModel root '{actual_root_node}' to '{target_maya_name}'.")
        cmds.parent(target_maya_name, consts.XMODELS_GROUP)
        LOG.info(f"Successfully imported and prepared XModel '{xmodel_name_from_json}' as '{target_maya_name}'.")
        return True

    def _add_xmodel_to_scene(self, xmodel_root_folder, xmodel_data, initial_suffix_count, bad_models_list):
        """
        Adds a single XModel to the Maya scene. Handles unique naming, duplication or import,
        and final positioning and scaling.

        Args:
            xmodel_root_folder (str): Root directory where XModels are stored.
            xmodel_data (dict): Data for the XModel (Name, PosX/Y/Z, RotX/Y/Z, Scale).
            initial_suffix_count (int): Starting count for generating unique names (usually 1).
            bad_models_list (list): List to append (model_name, error_message) tuples to if processing fails.
        """
        model_name_original = xmodel_data['Name']
        safe_maya_base_name = model_name_original.replace("/", "_").replace("@", "_").replace("-", "_")
        error_type_for_log = "unknown_error"

        try:
            target_maya_name, final_suffix_count = self._find_unique_maya_name(safe_maya_base_name, initial_suffix_count)

            was_duplicated = self._maybe_duplicate_existing(safe_maya_base_name, target_maya_name, final_suffix_count)

            if not was_duplicated:
                model_base_filename_for_path = os.path.basename(model_name_original)
                # Path construction: xmodel_root / original_name_path / basename_LOD0.ma
                # e.g., xmodels/weapons/gun/gun_LOD0.ma if model_name_original is "weapons/gun"
                model_file_path = os.path.join(xmodel_root_folder, model_name_original,
                                               f"{model_base_filename_for_path}{consts.XMODEL_LOD0_SUFFIX}")
                self._import_new_xmodel(model_file_path, target_maya_name, model_name_original)

            # Apply transformations
            pos = [float(xmodel_data['PosX']), float(xmodel_data['PosY']), float(xmodel_data['PosZ'])]
            rot = [float(xmodel_data.get('RotX', 0.0)), # Use .get for optional rotation
                   float(xmodel_data.get('RotY', 0.0)),
                   float(xmodel_data.get('RotZ', 0.0))]

            cmds.move(pos[0], pos[1], pos[2], target_maya_name, absolute=True)
            cmds.rotate(rot[0], rot[1], rot[2], target_maya_name, absolute=True)

            scale_val = float(xmodel_data['Scale']) * consts.INCHES_TO_CM
            cmds.scale(scale_val, scale_val, scale_val, target_maya_name, absolute=True)
            LOG.info(f"Placed and scaled XModel: '{model_name_original}' (Maya name: '{target_maya_name}').")

        except ValueError as e: # Specific errors from helpers (FileNotFound, NoRootNode)
            error_type_for_log = str(e)
            LOG.warning(f"Failed to add XModel '{model_name_original}': {error_type_for_log}")
            if not any(item[0] == model_name_original for item in bad_models_list):
                bad_models_list.append((model_name_original, error_type_for_log))
        except RuntimeError as e: # Maya command errors
            error_type_for_log = f"Maya runtime error: {e}"
            LOG.error(f"Runtime error processing XModel '{model_name_original}': {e}", exc_info=True)
            if not any(item[0] == model_name_original for item in bad_models_list):
                bad_models_list.append((model_name_original, error_type_for_log))
        except Exception as e: # Catch-all for other unexpected issues
            error_type_for_log = f"Unexpected error: {e}"
            LOG.error(f"Unexpected error processing XModel '{model_name_original}': {e}", exc_info=True)
            if not any(item[0] == model_name_original for item in bad_models_list):
                bad_models_list.append((model_name_original, error_type_for_log))
