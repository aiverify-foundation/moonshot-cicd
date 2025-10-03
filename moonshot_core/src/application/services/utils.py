from domain.services.logger import configure_logger

# Initialize a logger for this module
logger = configure_logger(__name__)

def load_module(loader, module_name: str, module_type, success_msg: str, error_msg: str):
    """
    Load a module using the specified loader.
    Args:
        loader: The loader to use for loading the module.
        module_name (str): The name of the module to be loaded.
        module_type: The type of the module to be loaded.
        success_msg (str): The success message to log.
        error_msg (str): The error message to log in case of failure.
    Returns:
        The loaded module instance, or None if loading fails.
    """
    try:
        # Load the module using the provided loader
        module_instance = loader.load(module_name, module_type)
        logger.info(success_msg)
        return module_instance
    except Exception as e:
        logger.error(error_msg.format(error=str(e)))
        raise e