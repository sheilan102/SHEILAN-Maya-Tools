"""
SHEILAN Tools Plugin for Maya.

Provides utility functions for other SHEILAN plugins, including:
- Centralized logging setup.
- File dialog wrappers.
- Maya menu creation for COD tools.

This plugin is loaded by Maya and initializes a top-level menu
"SHEILAN Tools" which provides access to various COD importers.
"""
import logging
import os

import maya.cmds as cmds
import maya.mel as mel
import maya.OpenMayaMPx as OpenMayaMPx

import cod_maya_tools_constants as consts

# Global dictionary to store initialized loggers
_loggers = {}


def get_logger(name=consts.DEFAULT_LOGGER_NAME, level=logging.INFO):
    """
    Configures and returns a logger instance.

    This function ensures that a logger with the same name is configured
    only once. Subsequent calls with the same name will return the
    existing logger instance.

    Args:
        name (str): The name for the logger. Defaults to `consts.DEFAULT_LOGGER_NAME`.
        level (int): The logging level (e.g., `logging.INFO`, `logging.DEBUG`).
                     Defaults to `logging.INFO`.

    Returns:
        logging.Logger: The configured logger instance.
    """
    if name in _loggers:
        return _loggers[name]

    logger_instance = logging.getLogger(name)
    logger_instance.setLevel(level)

    # Configure stream handler for Maya script editor output
    ch = logging.StreamHandler()
    ch.setLevel(level)
    formatter = logging.Formatter(consts.LOG_FORMAT)
    ch.setFormatter(formatter)

    # Add handler only if no handlers are already configured for this logger
    if not logger_instance.handlers:
        logger_instance.addHandler(ch)

    # Do not propagate messages to the root logger to avoid duplicate Maya console output
    logger_instance.propagate = False
    _loggers[name] = logger_instance
    return logger_instance


# Module-level logger instance
LOG = get_logger(__name__)


def _show_about_window(*args):
    """
    Presents the 'About' information window.
    Accepts `*args` because Maya menu commands pass an argument by default.
    """
    cmds.confirmDialog(
        message=consts.ABOUT_MESSAGE,
        button=['OK'],
        defaultButton='OK',
        title=consts.ABOUT_TITLE
    )


def _remove_menu():
    """Removes the plugin menu (consts.MENU_NAME) if it exists."""
    if cmds.control(consts.MENU_NAME, exists=True):
        LOG.info(f"Removing menu: {consts.MENU_NAME}")
        cmds.deleteUI(consts.MENU_NAME, menu=True)


def import_file_dialog(filter_str="", caption_str="", file_mode=1):
    """
    Asks the user for an input file or files using Maya's file dialog.

    Args:
        filter_str (str): The file filter string
                          (e.g., "Maya Files (*.ma *.mb);;All Files (*.*)").
        caption_str (str): The caption for the dialog window.
        file_mode (int): Determines the selection mode for the dialog.
            Common values:
            - 0: A single file that does not need to exist.
            - 1: A single file that must exist. (Default)
            - 2: Multiple files.
            - 3: A directory.
            - 4: A single file, allowing navigation into references or containers.

    Returns:
        str or list[str] or None: A string for a single file path,
                                   a list of strings for multiple file paths,
                                   or None if the dialog is cancelled.
                                   Paths are normalized using `os.path.normpath`.
    """
    import_from = cmds.fileDialog2(
        fileMode=file_mode,
        fileFilter=filter_str,
        caption=caption_str,
        dialogStyle=2  # Standard Maya dialog style
    )

    if not import_from or not import_from[0].strip():
        LOG.debug("File dialog cancelled by user.")
        return None

    if file_mode == 2:  # Multiple files
        paths = [os.path.normpath(p.strip()) for p in import_from if p.strip()]
        LOG.info(f"Files selected: {paths}")
        return paths
    else:  # Single file or directory
        path = import_from[0].strip()
        # Handle potential ".*" if it's part of a filter artifact
        if path.endswith(".*"):
            path = path[:-2]
        
        path = os.path.normpath(path)
        LOG.info(f"File or directory selected: {path}")
        return path


# --- Menu Command Functions ---

def _launch_cod_map_importer(*args):
    """Command to launch the COD Map Importer."""
    try:
        import codimporter # Local import to keep it self-contained if module is missing
        CODImporter_instance = codimporter.CODMAP()
        # If CODMAP() itself does the work in __init__, this is fine.
        # If it has an execute/run method, call that here.
        # Example: CODImporter_instance.run_import()
    except ImportError:
        LOG.error("Failed to import CODImporter. Ensure it's installed correctly.", exc_info=True)
    except Exception as e:
        LOG.error(f"Error launching COD Map Importer: {e}", exc_info=True)


def _launch_cod_xmodel_aligner(*args):
    """Command to launch the COD XModel Aligner."""
    try:
        import codxmodelalign # Local import
        XModelAlign_instance = codxmodelalign.XModelAlign()
        # Similar to CODMAP, if XModelAlign() runs in __init__, this is fine.
    except ImportError:
        LOG.error("Failed to import CODXModelAlign. Ensure it's installed correctly.", exc_info=True)
    except Exception as e:
        LOG.error(f"Error launching COD XModel Aligner: {e}", exc_info=True)


# --- Menu Creation ---

def _create_menu():
    """Creates the main plugin menu (consts.MENU_NAME) in Maya's main window."""
    _remove_menu()  # Ensure any existing menu is removed first

    LOG.info(f"Creating menu: {consts.MENU_NAME} ({consts.MENU_LABEL})")
    main_maya_window = mel.eval("$tmp = $gMainWindow") # Get Maya's main window
    cmds.setParent(main_maya_window)

    menu = cmds.menu(consts.MENU_NAME, label=consts.MENU_LABEL, tearOff=True)

    # COD Submenu
    cod_submenu = cmds.menuItem(label=consts.COD_SUBMENU_LABEL, subMenu=True, parent=menu)

    # COD Map Importer Menu Item
    try:
        import codimporter # Test import availability
        cmds.menuItem(
            label=consts.IMPORT_COD_MAP_LABEL,
            annotation="Imports a COD map with XModels.",
            command=_launch_cod_map_importer,
            parent=cod_submenu
        )
        LOG.debug(f"Added '{consts.IMPORT_COD_MAP_LABEL}' menu item.")
    except ImportError:
        LOG.warning("CODImporter module not found. 'Import COD Map' menu item will be disabled.")
        cmds.menuItem(
            label=consts.IMPORT_COD_MAP_UNAVAILABLE_LABEL,
            enable=False,
            parent=cod_submenu
        )

    # COD XModelAlign Menu Item
    try:
        import codxmodelalign # Test import availability
        cmds.menuItem(
            label=consts.IMPORT_FULLBODY_CHAR_LABEL,
            annotation="Aligns multi-part COD character models.",
            command=_launch_cod_xmodel_aligner,
            parent=cod_submenu
        )
        LOG.debug(f"Added '{consts.IMPORT_FULLBODY_CHAR_LABEL}' menu item.")
    except ImportError:
        LOG.warning("CODXModelAlign module not found. 'Import fullbody characters' menu item will be disabled.")
        cmds.menuItem(
            label=consts.IMPORT_FULLBODY_CHAR_UNAVAILABLE_LABEL,
            enable=False,
            parent=cod_submenu
        )

    # --- Standard Menu Items ---
    cmds.menuItem(divider=True, parent=menu)
    cmds.menuItem(label=consts.ABOUT_LABEL, command=_show_about_window, parent=menu)
    LOG.debug(f"Added '{consts.ABOUT_LABEL}' menu item.")


# --- Maya Plugin Lifecycle Functions ---

def initializePlugin(m_object):
    """
    Registers the plugin with Maya and creates the UI.
    This function is called by Maya when the plugin is loaded.

    Args:
        m_object (OpenMaya.MObject): A Maya API object representing this plugin.
    """
    plugin_version = getattr(consts, 'PLUGIN_VERSION', "Unknown")
    vendor_name = getattr(consts, 'VENDOR_NAME', "Unknown Vendor")
    plugin_name_display = f"{vendor_name} Tools - {consts.MENU_LABEL}"

    try:
        m_plugin = OpenMayaMPx.MFnPlugin(m_object, vendor_name, plugin_version, "Any")
        LOG.info(f"Initializing {plugin_name_display} version {plugin_version}...")
    except Exception as e:
        LOG.critical(f"Failed to initialize MFnPlugin for {plugin_name_display}: {e}", exc_info=True)
        # Depending on Maya version, MObject might not be valid if MFnPlugin init fails.
        # So, further cleanup or error reporting might be limited.
        raise # Re-raise to make Maya aware of the critical failure

    try:
        _create_menu()
        LOG.info(f"{consts.MENU_LABEL} plugin menu created successfully.")
    except Exception as e:
        LOG.error(f"Error during menu creation for {plugin_name_display}: {e}", exc_info=True)
        # Depending on severity, might want to raise to prevent partial plugin load.
        # For now, just log the error.


def uninitializePlugin(m_object):
    """
    Unregisters the plugin from Maya and cleans up UI and resources.
    This function is called by Maya when the plugin is unloaded.

    Args:
        m_object (OpenMaya.MObject): A Maya API object representing this plugin.
                                     (Note: MFnPlugin is typically not re-created here)
    """
    plugin_name_display = f"{getattr(consts, 'VENDOR_NAME', 'SHEILAN')} Tools - {consts.MENU_LABEL}"
    LOG.info(f"Uninitializing {plugin_name_display} plugin...")

    try:
        _remove_menu()
        LOG.info(f"{consts.MENU_LABEL} plugin menu removed.")
    except Exception as e:
        LOG.error(f"Error during menu removal for {plugin_name_display}: {e}", exc_info=True)

    # Clean up loggers managed by this plugin
    global _loggers
    LOG.debug("Cleaning up managed loggers...")
    for logger_name, logger_instance in list(_loggers.items()):
        LOG.debug(f"Removing handlers from logger: {logger_name}")
        for handler in list(logger_instance.handlers):
            try:
                handler.flush() # Ensure any buffered records are written
                handler.close() # Close the handler
                logger_instance.removeHandler(handler)
            except Exception as e:
                LOG.error(f"Error closing/removing handler for {logger_name}: {e}", exc_info=True)
    _loggers.clear()

    LOG.info(f"{plugin_name_display} uninitialization complete.")

# Notes for developers:
# - Constants: Ensure all user-facing strings and important identifiers
#   are defined in `cod_maya_tools_constants.py` for easy customization and localization.
# - Idempotence: `get_logger`, `_create_menu`, and `_remove_menu` are designed
#   to be idempotent (safe to call multiple times with the same outcome).
# - Error Handling: Menu item creation includes try-except blocks for imports
#   to prevent the entire plugin from failing if a submodule is missing.
#   The initializePlugin and uninitializePlugin functions also have try-except blocks.
# - Maya API Version: Assumes compatibility with Maya versions that support Python 2.7/3.x
#   and `OpenMayaMPx`. This version targets Python 3.
# - `import_file_dialog` is public. Callers in `codimporter.py` and `codxmodelalign.py`
#   have been updated in previous steps to use `SHEILAN_Tools.import_file_dialog`.
#   (The TODO comment about this was removed as it's now actioned).
