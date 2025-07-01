import json
import logging
import os
from typing import Any, Dict

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def safe_path_join(base_dir: str, *paths: str) -> str:
    """
    Safely joins path components, preventing directory traversal attacks.
    Ensures the resulting path is always within the base_dir.

    Args:
        base_dir: The base directory to restrict paths to.
        *paths: Variable number of path components to join.

    Returns:
        The securely joined and normalized absolute path.

    Raises:
        ValueError: If the resulting path attempts to traverse outside the base_dir.
    """
    combined_path = os.path.join(base_dir, *paths)
    normalized_path = os.path.normpath(combined_path)
    absolute_path = os.path.abspath(normalized_path)

    if not absolute_path.startswith(os.path.abspath(base_dir)):
        raise ValueError(f"Attempted directory traversal: {absolute_path} is not within {base_dir}")

    return absolute_path


def load_json_file(filepath: str) -> Dict[str, Any]:
    """
    Loads and parses a JSON file from the given filepath.

    Args:
        filepath: The absolute path to the JSON file.

    Returns:
        A dictionary containing the parsed JSON data.

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file content is not valid JSON.
        IOError: For other I/O related errors.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info(f"Successfully loaded JSON from: {filepath}")
        return data
    except FileNotFoundError:
        logger.error(f"Error: File not found at {filepath}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from {filepath}: {e}")
        raise
    except IOError as e:
        logger.error(f"Error reading file {filepath}: {e}")
        raise


def read_text_file(filepath: str) -> str:
    """
    Reads and returns the content of a text file.

    Args:
        filepath: The absolute path to the text file.

    Returns:
        The content of the file as a string.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: For other I/O related errors.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        logger.info(f"Successfully read text from: {filepath}")
        return content
    except FileNotFoundError:
        logger.error(f"Error: File not found at {filepath}")
        raise
    except IOError as e:
        logger.error(f"Error reading file {filepath}: {e}")
        raise
