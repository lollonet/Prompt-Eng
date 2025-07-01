import logging
import os
from typing import Any, Dict, List, Optional

from src.utils import load_json_file, read_text_file, safe_path_join

logger = logging.getLogger(__name__)


class KnowledgeManager:
    """
    Manages the loading and retrieval of best practices and tool information
    from the knowledge base. Implements caching for efficiency and uses safe path handling.
    """

    def __init__(self, config_path: str, base_path: Optional[str] = None):
        """
        Initializes the KnowledgeManager with the path to the tech stack mapping configuration.

        Args:
            config_path: The absolute path to the tech_stack_mapping.json file.
            base_path: Optional base path for the knowledge base root. If None, derived from config_path.
        """
        self.config_path = config_path
        self.tech_stack_mapping: Dict[str, Any] = self._load_tech_stack_mapping()
        # Determine the root of the knowledge base relative to the config file
        self.knowledge_base_root: str = (
            base_path if base_path else os.path.dirname(os.path.dirname(config_path))
        )
        self._cache: Dict[str, Any] = {}

    def _load_tech_stack_mapping(self) -> Dict[str, Any]:
        """
        Loads the tech stack mapping configuration file.

        Returns:
            A dictionary containing the tech stack mapping.
        """
        try:
            return load_json_file(self.config_path)
        except (FileNotFoundError, ValueError, IOError) as e:
            logger.error(f"Failed to load tech stack mapping from {self.config_path}: {e}")
            # Depending on criticality, might re-raise or return an empty dict
            return {}

    def get_best_practices(self, technology: str) -> List[str]:
        """
        Retrieves a list of best practice names associated with a given technology.

        Args:
            technology: The name of the technology (e.g., "python", "react").

        Returns:
            A list of best practice names. Returns an empty list if not found.
        """
        return self.tech_stack_mapping.get(technology, {}).get("best_practices", [])

    def get_tools(self, technology: str) -> List[str]:
        """
        Retrieves a list of tool names associated with a given technology.

        Args:
            technology: The name of the technology (e.g., "python", "docker").

        Returns:
            A list of tool names. Returns an empty list if not found.
        """
        return self.tech_stack_mapping.get(technology, {}).get("tools", [])

    def get_best_practice_details(self, bp_name: str) -> Optional[str]:
        """
        Retrieves the detailed content of a specific best practice from the knowledge base.
        Uses caching to avoid redundant file reads.

        Args:
            bp_name: The name of the best practice (e.g., "PEP8", "Clean Code Principles").

        Returns:
            The content of the best practice file as a string, or None if not found or an error occurs.
        """
        # Normalize name to match filename convention (lowercase, underscores)
        filename = f"{bp_name.lower().replace(' ', '_')}.md"
        filepath = safe_path_join(
            self.knowledge_base_root, "knowledge_base", "best_practices", filename
        )

        if filepath in self._cache:
            return self._cache[filepath]

        try:
            content = read_text_file(filepath)
            self._cache[filepath] = content
            return content
        except (FileNotFoundError, ValueError, IOError) as e:
            logger.warning(
                f"Could not load best practice details for '{bp_name}' from {filepath}: {e}"
            )
            return None

    def get_tool_details(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the detailed information of a specific tool from the knowledge base.
        Uses caching to avoid redundant file reads.

        Args:
            tool_name: The name of the tool (e.g., "Pylint", "Docker").

        Returns:
            A dictionary containing the tool's details, or None if not found or an error occurs.
        """
        # Normalize name to match filename convention (lowercase, underscores)
        filename = f"{tool_name.lower().replace(' ', '_')}.json"
        filepath = safe_path_join(self.knowledge_base_root, "knowledge_base", "tools", filename)

        if filepath in self._cache:
            return self._cache[filepath]

        try:
            content = load_json_file(filepath)
            self._cache[filepath] = content
            return content
        except (FileNotFoundError, ValueError, IOError) as e:
            logger.warning(f"Could not load tool details for '{tool_name}' from {filepath}: {e}")
            return None
