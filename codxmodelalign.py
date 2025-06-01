# -*- coding: utf-8 -*-
"""
COD XModelAlign Tool for Maya.

Provides a UI to import and assemble multi-part Call of Duty character models.
It aligns parts (head, body, legs, arms) based on game-specific (MW vs BO)
joint hierarchies and optionally runs associated MEL bind scripts.
"""
import os
import maya.cmds as cmds
import maya.mel as mel

import cod_maya_tools_constants as consts
import SHEILAN_Tools

LOG = SHEILAN_Tools.get_logger(__name__)


class XModelAlign(object):
    """
    Manages the UI and logic for importing and aligning multi-part character XModels.
    """

    def __init__(self):
        """
        Initializes the XModelAlign UI window.
        Sets up the window, layout, and UI controls for game mode selection
        and triggering the import process.
        """
        self.game_mode_optionmenu_name = consts.GAME_MODE_OPTIONMENU # UI name for the optionMenu

        # Ensure any existing window with the same name is closed to avoid conflicts
        if cmds.window(consts.CHAR_ALIGN_WINDOW_NAME, exists=True):
            cmds.deleteUI(consts.CHAR_ALIGN_WINDOW_NAME, window=True)

        self.win = cmds.window(consts.CHAR_ALIGN_WINDOW_NAME,
                               title=consts.CHAR_ALIGN_WINDOW_TITLE,
                               mnb=False, mxb=False, sizeable=False)

        # Main layout for the window
        cmds.columnLayout(parent=self.win, adjustableColumn=True,
                          rowSpacing=5, columnAttach=('both', 5))

        cmds.text(label='Select Game for Rig Conventions:', align='left')

        # Storing the full Maya path to the optionMenu control for reliable querying later
        self.ui_game_mode_option_menu = cmds.optionMenu(
            self.game_mode_optionmenu_name,
            label="Game:",
            changeCommand=self._log_new_menu_item_selection # For UI interaction debugging
        )
        cmds.menuItem(label=consts.GAME_MODE_MW)
        cmds.menuItem(label=consts.GAME_MODE_BO)

        cmds.separator(h=10, style='in')
        cmds.button(label='Load Full Body Model',
                    command=self._execute_model_import_and_align)
        cmds.separator(h=5, style='none') # Small spacer

        cmds.showWindow(self.win)
        LOG.info(f"'{consts.CHAR_ALIGN_WINDOW_TITLE}' window created and shown.")

    def _move_pivot(self, source_object, target_object):
        """
        Moves the pivot of `target_object` to the pivot of `source_object`.

        Uses `maya.cmds.xform` for pivot manipulation. This is a common utility
        for alignment tasks.

        Args:
            source_object (str): The name of the Maya object whose pivot provides the position.
            target_object (str): The name of the Maya object whose pivot will be moved.
        """
        try:
            if not cmds.objExists(source_object):
                LOG.error(f"_move_pivot: Source object '{source_object}' does not exist. Cannot move pivot.")
                return
            if not cmds.objExists(target_object):
                LOG.error(f"_move_pivot: Target object '{target_object}' does not exist. Cannot move pivot.")
                return

            pivot_position = cmds.xform(source_object, query=True, worldSpace=True, rotatePivot=True)
            cmds.xform(target_object, worldSpace=True, pivots=pivot_position) # Set both rotate and scale pivots
            LOG.debug(f"Moved pivot of '{target_object}' to {pivot_position} (from '{source_object}').")
        except RuntimeError as e:
            LOG.error(f"Maya runtime error in _move_pivot (source: '{source_object}', target: '{target_object}'): {e}",
                      exc_info=True)
        except Exception as e:
            LOG.error(f"Unexpected error in _move_pivot: {e}", exc_info=True)

    def _rig_model_part(self, model_part_file_path=""):
        """
        Sources an external MEL script assumed to be a bind script for the given model part.

        The bind script is conventionally named like the model's .ma file but with
        a `_BIND.mel` suffix (e.g., `model_head.ma` -> `model_head_BIND.mel`).

        Args:
            model_part_file_path (str): The file path to the model part's .ma file,
                                        from which the MEL script name is derived.

        Important Note:
            This method executes external MEL code. The contents and behavior of these
            MEL scripts are not managed by this Python tool. They are typically used for
            skinning operations (e.g., `skinCluster`). For improved robustness and
            integration, translating these MEL scripts into Python `maya.cmds` would be
            the ideal long-term solution. This current implementation provides logging
            around the MEL execution for better observability.
        """
        if not model_part_file_path or not isinstance(model_part_file_path, str):
            LOG.error("_rig_model_part: Invalid or empty `model_part_file_path` provided.")
            return

        rig_script_path = model_part_file_path.lower().replace(".ma", consts.RIG_SCRIPT_SUFFIX).replace("\\", "/")

        if not os.path.exists(rig_script_path):
            LOG.warning(f"Rig MEL script not found (expected at: '{rig_script_path}'). Skipping rigging for this part.")
            return

        LOG.info(f"Attempting to source MEL bind script: '{rig_script_path}'")
        try:
            mel.eval(f'source "{rig_script_path}"') # Execute the MEL script
            LOG.info(f"Successfully sourced MEL script: '{rig_script_path}'.")
        except RuntimeError as e: # Maya's typical error for MEL failures
            LOG.error(f"Runtime error sourcing MEL script '{rig_script_path}': {e}", exc_info=True)
        except Exception as e: # Other potential Python errors during the eval call
            LOG.error(f"Unexpected Python error when trying to source MEL script '{rig_script_path}': {e}", exc_info=True)

    def _load_and_rename_model_part(self, file_path, part_name_prefix, unique_suffix):
        """
        Loads a model part from a .ma file into Maya and renames its main components
        (identified mesh transform and skeleton root) according to conventions.

        Args:
            file_path (str): Full path to the .ma file for the model part.
            part_name_prefix (str): The base name for this part (e.g., "head", "body").
                                    Used to construct final Maya object names.
            unique_suffix (int or str): A suffix (usually an integer) to ensure unique
                                        names in the Maya scene.

        Returns:
            bool: True if loading and primary renaming steps were successful, False otherwise.
                  Note: Minor warnings during heuristic-based renaming might still result in True.
        """
        if not file_path or not os.path.exists(file_path):
            LOG.error(f"_load_and_rename_model_part: File not found for part '{part_name_prefix}': '{file_path}'.")
            return False

        LOG.debug(f"Loading model part '{part_name_prefix}' (suffix: {unique_suffix}) from: '{file_path}'")
        try:
            imported_nodes = cmds.file(file_path, i=True, returnNewNodes=True, defaultNamespace=True)
            if not imported_nodes:
                LOG.warning(f"No nodes returned by Maya after importing '{file_path}'. The file might be empty or problematic.")
                return False
            LOG.info(f"Imported '{part_name_prefix}' from '{file_path}'. Imported nodes: {imported_nodes}")

            model_name_from_file = os.path.basename(file_path).split(".")[0].lower()
            top_transform_node = None

            for node in imported_nodes:
                if cmds.nodeType(node) == 'transform' and not cmds.listRelatives(node, parent=True, fullPath=True):
                    node_short_name = node.split(':')[-1]
                    if model_name_from_file in node_short_name.lower():
                        top_transform_node = node
                        break
            if not top_transform_node:
                for node in imported_nodes: # Fallback: first top-level transform
                    if cmds.nodeType(node) == 'transform' and not cmds.listRelatives(node, parent=True, fullPath=True):
                        top_transform_node = node
                        LOG.debug(f"No filename match for top transform of '{part_name_prefix}'; "
                                  f"using first found: '{top_transform_node}'.")
                        break

            final_mesh_name = f"{part_name_prefix}{consts.MESH_SUFFIX}{unique_suffix}"
            if top_transform_node:
                try:
                    cmds.rename(top_transform_node, final_mesh_name)
                    LOG.debug(f"Renamed top transform '{top_transform_node}' to '{final_mesh_name}'.")
                except RuntimeError as e:
                     LOG.error(f"Failed to rename '{top_transform_node}' to '{final_mesh_name}': {e}. Name clash likely.")
            else:
                LOG.warning(f"Could not identify a distinct top-level mesh transform for '{part_name_prefix}' "
                            f"from '{file_path}'. Manual check may be needed.")

            joint_root_node = None
            for node in imported_nodes:
                node_short_name = node.split(':')[-1]
                if cmds.nodeType(node) == 'joint' and not cmds.listRelatives(node, parent=True, fullPath=True):
                    if consts.JOINTS_OBJECT_NAME.lower() in node_short_name.lower():
                        joint_root_node = node
                        break
            if not joint_root_node:
                 for node in imported_nodes: # Fallback: first top-level joint
                    if cmds.nodeType(node) == 'joint' and not cmds.listRelatives(node, parent=True, fullPath=True):
                        joint_root_node = node
                        LOG.debug(f"No joint named '{consts.JOINTS_OBJECT_NAME}' found for '{part_name_prefix}'; "
                                  f"using first top-level joint: '{joint_root_node}'.")
                        break

            final_skeleton_name = f"{part_name_prefix}{consts.SKELETON_SUFFIX}{unique_suffix}"
            if joint_root_node:
                try:
                    cmds.rename(joint_root_node, final_skeleton_name)
                    LOG.debug(f"Renamed joint root '{joint_root_node}' to '{final_skeleton_name}'.")
                except RuntimeError as e:
                    LOG.error(f"Failed to rename '{joint_root_node}' to '{final_skeleton_name}': {e}. Name clash likely.")
            else:
                 LOG.warning(f"Could not identify or rename a skeleton root (expected like '{consts.JOINTS_OBJECT_NAME}') "
                             f"for part '{part_name_prefix}' from '{file_path}'.")
            return True # Considered successful if import happened, even with minor rename issues.

        except RuntimeError as e:
            LOG.error(f"Maya runtime error loading model part '{part_name_prefix}' from '{file_path}': {e}", exc_info=True)
            return False
        except Exception as e:
            LOG.error(f"Unexpected error loading model part '{part_name_prefix}' from '{file_path}': {e}", exc_info=True)
            return False

    def _get_part_file_paths(self, body_file_path, body_filename_lower, base_part_placeholder_in_file):
        """
        Constructs expected file paths for associated character model parts.

        Args:
            body_file_path (str): Full path to the primary body/torso .ma file.
            body_filename_lower (str): Lowercased filename of the body/torso .ma file.
            base_part_placeholder_in_file (str): The identifying string in the body filename
                                                 (e.g., `_torso`, `_body`) that will be replaced
                                                 to find other parts.

        Returns:
            dict: Maps part type (str, e.g., "head") to its expected full file path (str).
        """
        body_dir = os.path.dirname(body_file_path)
        part_paths = {
            "head": os.path.join(body_dir, body_filename_lower.replace(base_part_placeholder_in_file, consts.PART_HEAD)),
            "legs": os.path.join(body_dir, body_filename_lower.replace(base_part_placeholder_in_file, consts.PART_LEGS)),
            "arms": os.path.join(body_dir, body_filename_lower.replace(base_part_placeholder_in_file, consts.PART_ARMS))
        }
        LOG.debug(f"Derived associated part file paths: {part_paths}")
        return part_paths

    def _execute_model_import_and_align(self, *args):
        """
        Main private method orchestrating the character import and alignment.
        This is triggered by the UI button. It handles file selection, loading parts,
        aligning them based on game mode, and final rigging/cleanup.
        """
        LOG.info("Starting full character model import and alignment process...")
        game_mode = cmds.optionMenu(self.ui_game_mode_option_menu, query=True, value=True)
        LOG.info(f"Selected game mode for alignment: {game_mode}")

        model_count_suffix = self._find_next_available_model_suffix()

        body_file_path = SHEILAN_Tools.import_file_dialog(
            consts.MAYA_FILES_FILTER, "Load Main Body/Torso Model File", 1) # Mode 1: file must exist

        if not body_file_path:
            LOG.warning("No body/torso model file selected. Aborting import process.")
            return

        body_file_path = os.path.normpath(body_file_path)
        body_filename_lower = os.path.basename(body_file_path).lower()

        body_part_prefix = "body" # Standardized internal prefix for the main body component
        base_part_filename_token = None # The token in the filename like "_torso" or "_body"
        if consts.PART_TORSO in body_filename_lower:
            base_part_filename_token = consts.PART_TORSO
        elif consts.PART_BODY in body_filename_lower:
            base_part_filename_token = consts.PART_BODY
        else:
            LOG.error(f"Selected body file '{body_filename_lower}' must include a recognizable part token "
                      f"like '{consts.PART_TORSO}' or '{consts.PART_BODY}' in its filename for part discovery.")
            return

        LOG.info(f"Loading main body part: {body_file_path} (using '{body_part_prefix}' as internal prefix)")
        if not self._load_and_rename_model_part(body_file_path, body_part_prefix, model_count_suffix):
             LOG.critical(f"Failed to load the primary body/torso model: '{body_file_path}'. Aborting.")
             return

        part_file_paths = self._get_part_file_paths(body_file_path, body_filename_lower, base_part_filename_token)

        # Load and align Head
        head_file = part_file_paths["head"]
        if os.path.exists(head_file):
            LOG.info(f"Loading head part: {head_file}")
            if self._load_and_rename_model_part(head_file, "head", model_count_suffix): # "head" is prefix
                self._align_head(model_count_suffix, game_mode, body_part_prefix)
            else: LOG.warning(f"Could not load head model from '{head_file}'. Alignment skipped.")
        else: LOG.warning(f"Head model file not found (expected at '{head_file}'). Head part skipped.")

        # Black Ops mode specific parts (legs, arms)
        if game_mode == consts.GAME_MODE_BO:
            LOG.info("Black Ops game mode: processing legs and arms.")
            current_body_skeleton_name = f"{body_part_prefix}{consts.SKELETON_SUFFIX}{model_count_suffix}"

            hip_le_joint = f"{current_body_skeleton_name}|{consts.JOINT_MAIN_ROOT}|{consts.JOINT_HIP_LE}"
            hip_ri_joint = f"{current_body_skeleton_name}|{consts.JOINT_MAIN_ROOT}|{consts.JOINT_HIP_RI}"
            if cmds.objExists(hip_le_joint): cmds.delete(hip_le_joint); LOG.debug(f"Deleted '{hip_le_joint}'.")
            if cmds.objExists(hip_ri_joint): cmds.delete(hip_ri_joint); LOG.debug(f"Deleted '{hip_ri_joint}'.")

            legs_file = part_file_paths["legs"]
            if os.path.exists(legs_file):
                LOG.info(f"Loading legs part: {legs_file}")
                if self._load_and_rename_model_part(legs_file, "legs", model_count_suffix): # "legs" as prefix
                    self._align_legs(model_count_suffix, body_part_prefix)
                else: LOG.warning(f"Could not load legs model from '{legs_file}'. Alignment skipped.")
            else: LOG.warning(f"Legs model file not found (expected at '{legs_file}'). Legs part skipped.")

            arms_file = part_file_paths["arms"]
            if os.path.exists(arms_file):
                LOG.info(f"Loading arms part: {arms_file}")
                if self._load_and_rename_model_part(arms_file, "arms", model_count_suffix): # "arms" as prefix
                    self._align_arms(model_count_suffix, body_part_prefix)
                else: LOG.warning(f"Could not load arms model from '{arms_file}'. Alignment skipped.")
            else: LOG.warning(f"Arms model file not found (expected at '{arms_file}'). Arms part skipped.")

        # Final rename of the (potentially now combined) main body skeleton
        initial_body_skeleton_name = f"{body_part_prefix}{consts.SKELETON_SUFFIX}{model_count_suffix}"
        final_player_skeleton_name = f"{consts.PLAYER_MODEL_PREFIX}{model_count_suffix}{consts.SKELETON_SUFFIX}"
        if cmds.objExists(initial_body_skeleton_name):
             if initial_body_skeleton_name != final_player_skeleton_name: # Avoid renaming if already correct
                cmds.rename(initial_body_skeleton_name, final_player_skeleton_name)
                LOG.info(f"Main skeleton '{initial_body_skeleton_name}' renamed to '{final_player_skeleton_name}'.")
             else:
                LOG.info(f"Main skeleton already named '{final_player_skeleton_name}'. No rename needed.")
        else:
            # This might happen if the body part itself failed to load its skeleton correctly.
            LOG.error(f"Main body skeleton '{initial_body_skeleton_name}' not found for final renaming. "
                      "The character hierarchy may be incomplete.")

        # Run rigging scripts for all successfully loaded and potentially aligned parts
        LOG.info("Running rigging scripts for all applicable model parts...")
        self._rig_model_part(body_file_path)
        if os.path.exists(head_file): self._rig_model_part(head_file)
        if game_mode == consts.GAME_MODE_BO: # Only rig these if in BO mode and files existed
            if os.path.exists(part_file_paths["legs"]): self._rig_model_part(part_file_paths["legs"])
            if os.path.exists(part_file_paths["arms"]): self._rig_model_part(part_file_paths["arms"])

        self._cleanup_color_sets()
        LOG.info(f"Character import and alignment process finished for: {consts.PLAYER_MODEL_PREFIX}{model_count_suffix}.")

    def _cleanup_color_sets(self):
        """
        Deletes all color sets from meshes that are identified by having
        `consts.WRAITHMESH_IDENTIFIER` in their transform node's name.
        """
        LOG.debug("Cleaning up color sets from identified WraithMeshes...")
        all_meshes_in_scene = cmds.ls(type='mesh', long=True)
        if not all_meshes_in_scene:
            LOG.debug("No meshes found in scene, skipping color set cleanup.")
            return

        cleaned_count = 0
        for mesh_shape_node in all_meshes_in_scene:
            # Get the transform node (parent) of the mesh shape
            transform_nodes = cmds.listRelatives(mesh_shape_node, parent=True, fullPath=True)
            if not transform_nodes:
                continue # Should not happen for valid meshes

            transform_node_path = transform_nodes[0]
            # Check if the identifier is in any part of the transform node's full path
            if consts.WRAITHMESH_IDENTIFIER in transform_node_path:
                try:
                    all_color_sets = cmds.polyColorSet(mesh_shape_node, query=True, allColorSets=True)
                    if all_color_sets:
                        for cs_name in all_color_sets:
                            cmds.polyColorSet(mesh_shape_node, delete=True, colorSet=cs_name)
                        LOG.debug(f"Deleted color sets from '{mesh_shape_node}' (parent: '{transform_node_path}').")
                        cleaned_count +=1
                except Exception as e:
                    LOG.warning(f"Could not delete color sets from '{mesh_shape_node}': {e}", exc_info=True)
        if cleaned_count > 0:
            LOG.info(f"Color sets cleaned from {cleaned_count} WraithMesh identified meshes.")
        else:
            LOG.debug("No meshes matching WraithMesh identifier found or they had no color sets.")

    def _find_next_available_model_suffix(self):
        """
        Finds the next available integer suffix for naming player models uniquely
        (e.g., if 'playermodel1_skeleton' exists, returns 2).

        Returns:
            int: The next available unique suffix number (e.g., 1, 2, 3...).
        """
        count = 1
        while cmds.objExists(f'{consts.PLAYER_MODEL_PREFIX}{count}{consts.SKELETON_SUFFIX}'):
            count += 1
        LOG.debug(f"Next available player model suffix number: {count}")
        return count

    def _align_head(self, model_suffix, game_mode, body_part_prefix):
        """
        Aligns the loaded head model part to the main body skeleton based on game mode conventions.

        Args:
            model_suffix (int or str): The unique suffix for the current model.
            game_mode (str): The selected game mode (e.g., consts.GAME_MODE_MW).
            body_part_prefix (str): The prefix used for the main body part's skeleton
                                    (e.g., "body"). This is used to find the reference
                                    skeleton before it's potentially renamed to the final
                                    player model name.
        """
        LOG.info(f"Aligning head for model '{consts.PLAYER_MODEL_PREFIX}{model_suffix}', game mode: {game_mode}.")
        head_mesh = f"head{consts.MESH_SUFFIX}{model_suffix}"
        head_skeleton = f"head{consts.SKELETON_SUFFIX}{model_suffix}"

        # Determine the current name of the main body skeleton to align against.
        # It might be body_skeleton<N> or already renamed to playermodel<N>_skeleton if BO parts were processed.
        body_skeleton_initial_name = f"{body_part_prefix}{consts.SKELETON_SUFFIX}{model_suffix}"
        body_skeleton_final_name = f"{consts.PLAYER_MODEL_PREFIX}{model_suffix}{consts.SKELETON_SUFFIX}"

        body_skeleton_ref = body_skeleton_initial_name
        if cmds.objExists(body_skeleton_final_name): # Prefer final name if it exists
            body_skeleton_ref = body_skeleton_final_name
        elif not cmds.objExists(body_skeleton_initial_name): # If neither exists, error
             LOG.error(f"alignHead: Main body skeleton ('{body_skeleton_initial_name}' or '{body_skeleton_final_name}') not found. Cannot align head.")
             return

        if not all(cmds.objExists(name) for name in [head_mesh, head_skeleton]):
            LOG.error(f"alignHead: Head mesh ('{head_mesh}') or head skeleton ('{head_skeleton}') not found. Skipping head alignment.")
            return

        # Use a temporary group for alignment to manage transformations cleanly
        alignment_group_name = consts.HEAD_ALIGN_GROUP
        if cmds.objExists(alignment_group_name): cmds.delete(alignment_group_name) # Clean up if exists
        cmds.group(em=True, name=alignment_group_name, world=True)

        try:
            cmds.parent(head_mesh, head_skeleton, alignment_group_name)
        except RuntimeError as e:
            LOG.error(f"Failed to parent head parts to alignment group '{alignment_group_name}': {e}")
            if cmds.objExists(alignment_group_name): cmds.delete(alignment_group_name)
            return

        head_pivot_joint_rel_path, body_target_joint_rel_path = "", ""
        head_alignment_rotation = None

        if game_mode == consts.GAME_MODE_MW:
            head_pivot_joint_rel_path = f"|{consts.JOINT_SPINE_4}"
            body_target_joint_rel_path = consts.MW_BODY_JOINT_CHAIN_FOR_HEAD
        elif game_mode == consts.GAME_MODE_BO:
            head_pivot_joint_rel_path = f"|{consts.TAG_ORIGIN}|{consts.JOINT_MAIN_ROOT}|{consts.JOINT_SPINE_LOWER}|{consts.JOINT_SPINE_UPPER}|{consts.JOINT_SPINE_4}"
            body_target_joint_rel_path = consts.BO_BODY_JOINT_CHAIN_FOR_HEAD
            head_alignment_rotation = consts.HEAD_ROTATION_BO
        else:
            LOG.error(f"alignHead: Unknown game mode '{game_mode}'. Cannot determine joint paths.")
            self._cleanup_alignment_group(alignment_group_name, [head_mesh, head_skeleton])
            return

        # Construct full paths to joints for robust operations
        full_head_pivot_joint = f"{head_skeleton}{head_pivot_joint_rel_path}"
        full_body_target_joint = f"{body_skeleton_ref}{body_target_joint_rel_path}"

        if not cmds.objExists(full_head_pivot_joint) or not cmds.objExists(full_body_target_joint):
            LOG.error(f"alignHead: Critical alignment joints not found. Head Pivot: '{full_head_pivot_joint}', "
                      f"Body Target: '{full_body_target_joint}'. Skipping head alignment.")
            self._cleanup_alignment_group(alignment_group_name, [head_mesh, head_skeleton])
            return

        self._move_pivot(full_head_pivot_joint, alignment_group_name)
        constraint = cmds.parentConstraint(full_body_target_joint, alignment_group_name, maintainOffset=False)[0]
        if head_alignment_rotation:
            cmds.rotate(head_alignment_rotation[0], head_alignment_rotation[1], head_alignment_rotation[2],
                        alignment_group_name, absolute=True, worldSpace=True) # Ensure world space for absolute rotation post-constraint
        cmds.delete(constraint)

        # Reparent the head's neck structure to the body's spine
        body_neck_attach_point = full_body_target_joint # Typically ...|j_spine4
        head_neck_joint_to_move = f"{head_skeleton}{head_pivot_joint_rel_path}|{consts.JOINT_NECK}" # Neck under the pivot

        existing_body_neck_joint = f"{body_neck_attach_point}|{consts.JOINT_NECK}"
        if cmds.objExists(existing_body_neck_joint):
            try:
                cmds.delete(existing_body_neck_joint)
                LOG.debug(f"Deleted existing neck joint '{existing_body_neck_joint}' from body skeleton.")
            except Exception as e: LOG.warning(f"Could not delete existing body neck '{existing_body_neck_joint}': {e}")

        if cmds.objExists(head_neck_joint_to_move):
            try:
                cmds.parent(head_neck_joint_to_move, body_neck_attach_point)
                LOG.debug(f"Parented head's neck structure '{head_neck_joint_to_move}' to '{body_neck_attach_point}'.")
            except Exception as e: LOG.error(f"Failed to parent head's neck structure: {e}", exc_info=True)
        else: LOG.warning(f"Head's neck joint structure '{head_neck_joint_to_move}' not found for reparenting.")

        # Cleanup: unparent mesh, then delete the original head skeleton root (now empty or parts reparented) and the alignment group.
        self._cleanup_alignment_group(alignment_group_name, [head_mesh], items_to_delete_with_group=[head_skeleton])
        LOG.info("Head alignment process complete.")

    def _align_arms(self, model_suffix, body_part_prefix):
        """
        Aligns the loaded arms model part to the main body skeleton (primarily for BO characters).
        Similar to head alignment, uses temporary groups and specific joint paths.

        Args:
            model_suffix (int or str): The unique suffix for the current model.
            body_part_prefix (str): Prefix for the main body part (unused here as BO expects final player model name).
        """
        LOG.info(f"Aligning arms for model '{consts.PLAYER_MODEL_PREFIX}{model_suffix}'.")
        arms_mesh = f"arms{consts.MESH_SUFFIX}{model_suffix}"
        arms_skeleton = f"arms{consts.SKELETON_SUFFIX}{model_suffix}"
        body_skeleton_ref = f"{consts.PLAYER_MODEL_PREFIX}{model_suffix}{consts.SKELETON_SUFFIX}" # BO typically uses final name

        if not all(cmds.objExists(name) for name in [arms_mesh, arms_skeleton, body_skeleton_ref]):
            LOG.error(f"alignArms: Missing required parts. ArmsMesh: '{arms_mesh}', ArmsSkel: '{arms_skeleton}', "
                      f"BodySkel: '{body_skeleton_ref}'. Skipping arms alignment.")
            return

        alignment_group_name = consts.ARMS_ALIGN_GROUP
        if cmds.objExists(alignment_group_name): cmds.delete(alignment_group_name)
        cmds.group(em=True, name=alignment_group_name, world=True)
        try:
            cmds.parent(arms_mesh, arms_skeleton, alignment_group_name)
        except RuntimeError as e:
            LOG.error(f"Failed to parent arm parts to alignment group '{alignment_group_name}': {e}")
            if cmds.objExists(alignment_group_name): cmds.delete(alignment_group_name)
            return

        full_arm_pivot_joint = f"{arms_skeleton}{consts.BO_ARM_PIVOT_JOINT_REL}"
        full_body_target_joint = f"{body_skeleton_ref}{consts.BO_BODY_TARGET_FOR_ARM_REL}"

        if not cmds.objExists(full_arm_pivot_joint) or not cmds.objExists(full_body_target_joint):
            LOG.error(f"alignArms: Critical alignment joints not found. Arm Pivot: '{full_arm_pivot_joint}', "
                      f"Body Target: '{full_body_target_joint}'. Skipping arms alignment.")
            self._cleanup_alignment_group(alignment_group_name, [arms_mesh, arms_skeleton])
            return

        self._move_pivot(full_arm_pivot_joint, alignment_group_name)
        constraint = cmds.parentConstraint(full_body_target_joint, alignment_group_name, maintainOffset=False)[0]
        cmds.rotate(consts.ARMS_ROTATION_BO[0], consts.ARMS_ROTATION_BO[1], consts.ARMS_ROTATION_BO[2],
                    alignment_group_name, absolute=True, worldSpace=True)
        cmds.delete(constraint)

        # Reparenting clavicles from arms skeleton to body skeleton's spine
        body_clavicle_attach_point = f"{body_skeleton_ref}{consts.BO_BODY_CLAVICLE_PARENT}"
        arm_clav_le_to_move = f"{arms_skeleton}{consts.BO_ARM_CLAVICLE_LE_REL}"
        arm_clav_ri_to_move = f"{arms_skeleton}{consts.BO_ARM_CLAVICLE_RI_REL}"

        existing_body_clav_le = f"{body_clavicle_attach_point}|{consts.JOINT_CLAVICLE_LE}"
        existing_body_clav_ri = f"{body_clavicle_attach_point}|{consts.JOINT_CLAVICLE_RI}"

        if cmds.objExists(existing_body_clav_le): cmds.delete(existing_body_clav_le)
        if cmds.objExists(existing_body_clav_ri): cmds.delete(existing_body_clav_ri)

        if cmds.objExists(arm_clav_le_to_move): cmds.parent(arm_clav_le_to_move, body_clavicle_attach_point)
        else: LOG.warning(f"Arm's left clavicle '{arm_clav_le_to_move}' not found for reparenting.")
        if cmds.objExists(arm_clav_ri_to_move): cmds.parent(arm_clav_ri_to_move, body_clavicle_attach_point)
        else: LOG.warning(f"Arm's right clavicle '{arm_clav_ri_to_move}' not found for reparenting.")

        self._cleanup_alignment_group(alignment_group_name, [arms_mesh], items_to_delete_with_group=[arms_skeleton])
        LOG.info("Arms alignment process complete.")

    def _align_legs(self, model_suffix, body_part_prefix):
        """
        Aligns (reparents) joints from the loaded legs skeleton to the main body skeleton.
        This is primarily for BO characters where legs are separate.

        Args:
            model_suffix (int or str): The unique suffix for the current model.
            body_part_prefix (str): Prefix for the main body part (unused here as BO expects final player model name).
        """
        LOG.info(f"Aligning legs for model '{consts.PLAYER_MODEL_PREFIX}{model_suffix}'.")
        legs_skeleton = f"legs{consts.SKELETON_SUFFIX}{model_suffix}"
        body_skeleton_ref = f"{consts.PLAYER_MODEL_PREFIX}{model_suffix}{consts.SKELETON_SUFFIX}"

        if not cmds.objExists(legs_skeleton) or not cmds.objExists(body_skeleton_ref):
            LOG.error(f"alignLegs: Skeletons not found. LegsSkel: '{legs_skeleton}', BodySkel: '{body_skeleton_ref}'. Skipping legs alignment.")
            return

        body_main_root_attach_point = f"{body_skeleton_ref}|{consts.JOINT_MAIN_ROOT}"
        legs_main_root_source = f"{legs_skeleton}|{consts.JOINT_MAIN_ROOT}"

        if not cmds.objExists(body_main_root_attach_point) or not cmds.objExists(legs_main_root_source):
            LOG.error(f"alignLegs: Main root not found in BodySkel ('{body_main_root_attach_point}') or "
                      f"LegsSkel ('{legs_main_root_source}'). Cannot reparent leg joints.")
            return

        child_joints_of_legs_root = cmds.listRelatives(legs_main_root_source, children=True, fullPath=True, type='joint') or []

        LOG.debug(f"Found leg child joints to reparent: {child_joints_of_legs_root}")
        for joint_to_move in child_joints_of_legs_root:
            short_name = joint_to_move.split('|')[-1]
            target_joint_on_body = f"{body_main_root_attach_point}|{short_name}"

            if cmds.objExists(target_joint_on_body): # If a joint by this name already exists on body
                LOG.warning(f"Joint '{short_name}' already exists under '{body_main_root_attach_point}'. Deleting existing one before reparenting.")
                try: cmds.delete(target_joint_on_body)
                except Exception as e: LOG.error(f"Failed to delete existing joint '{target_joint_on_body}' on body: {e}")

            try:
                cmds.parent(joint_to_move, body_main_root_attach_point)
                LOG.debug(f"Parented leg joint '{joint_to_move}' to '{body_main_root_attach_point}'.")
            except RuntimeError as e:
                LOG.error(f"Could not parent leg joint '{joint_to_move}' to '{body_main_root_attach_point}': {e}", exc_info=True)

        if not child_joints_of_legs_root:
            LOG.warning(f"No child joints found under legs root '{legs_main_root_source}' to reparent.")

        # Delete the old legs skeleton hierarchy (should be empty or parts reparented)
        if cmds.objExists(legs_skeleton):
            try:
                cmds.delete(legs_skeleton)
                LOG.debug(f"Deleted original legs skeleton '{legs_skeleton}'.")
            except Exception as e: LOG.error(f"Failed to delete original legs skeleton '{legs_skeleton}': {e}")
        LOG.info("Legs alignment process complete.")

    def _cleanup_alignment_group(self, group_name, items_to_unparent=None, items_to_delete_with_group=None):
        """
        Safely unparents specified items from a group and then deletes the group.
        Optionally, some items can be left in the group to be deleted with it (e.g., old skeleton roots).

        Args:
            group_name (str): The name of the alignment group to delete.
            items_to_unparent (list, optional): List of item names to parent to the world
                                                before deleting the group.
            items_to_delete_with_group (list, optional): List of item names that are children
                                                         of the group and should be deleted
                                                         along with it. This is more for logging
                                                         or explicit intent; they would be deleted
                                                         anyway if they are children.
        """
        if not cmds.objExists(group_name):
            LOG.debug(f"_cleanup_alignment_group: Group '{group_name}' does not exist. Nothing to do.")
            return

        if items_to_unparent:
            for item in items_to_unparent:
                if cmds.objExists(item):
                    item_parent = cmds.listRelatives(item, parent=True, fullPath=True)
                    if item_parent and item_parent[0].endswith(f"|{group_name}"): # Check if it's a direct child
                        try:
                            cmds.parent(item, world=True)
                            LOG.debug(f"Unparented '{item}' from '{group_name}'.")
                        except RuntimeError as e:
                             LOG.warning(f"Failed to unparent '{item}' from '{group_name}': {e}")
                    else:
                        LOG.debug(f"Item '{item}' is not a direct child of '{group_name}', not unparenting.")
                else:
                    LOG.debug(f"Item '{item}' to unparent does not exist.")

        # Log items intended for deletion with the group (if provided)
        if items_to_delete_with_group:
            for item in items_to_delete_with_group:
                 if cmds.objExists(item) and cmds.listRelatives(item, parent=True, fullPath=True)[0].endswith(f"|{group_name}"):
                    LOG.debug(f"Item '{item}' will be deleted with group '{group_name}'.")

        try:
            cmds.delete(group_name)
            LOG.debug(f"Deleted alignment group '{group_name}'.")
        except RuntimeError as e:
            LOG.error(f"Failed to delete alignment group '{group_name}': {e}", exc_info=True)

    def _log_new_menu_item_selection(self, selected_item):
        """
        Callback for the game mode OptionMenu to log the new selection.
        Primarily for UI debugging.

        Args:
            selected_item (str): The label of the newly selected menu item.
        """
        LOG.debug(f"Game mode OptionMenu selection changed to: '{selected_item}'.")
        # The return value of a changeCommand is not typically used by Maya,
        # but returning it doesn't hurt.
        return selected_item
