import logging
from typing import Any, Dict, List, Optional
from jinja2 import Environment, FileSystemLoader
from src.knowledge_manager import KnowledgeManager

logger = logging.getLogger(__name__)

class PromptGenerator:
    """
    Generates prompts for LLMs based on specified technologies, task types,
    and code requirements, incorporating detailed best practices and tool information.
    """
    def __init__(self, prompts_dir: str, config_path: str):
        """
        Initializes the PromptGenerator.

        Args:
            prompts_dir: The absolute path to the directory containing prompt templates.
            config_path: The absolute path to the tech_stack_mapping.json file.
        """
        self.env = Environment(loader=FileSystemLoader(prompts_dir))
        self.knowledge_manager = KnowledgeManager(config_path)

    def generate_prompt(
        self,
        technologies: List[str],
        task_type: str,
        code_requirements: str,
        task_description: str = "",
        template_name: str = "base_prompts/generic_code_prompt.txt",
    ) -> str:
        """
        Generates a formatted prompt string based on the provided parameters.

        Args:
            technologies: A list of technologies (e.g., languages, frameworks, tools)
                          relevant to the task.
            task_type: The general type of task (e.g., "new feature", "bug fix").
            code_requirements: Specific requirements for the generated code.
            task_description: A detailed description of the task.
            template_name: The name of the Jinja2 template to use (relative to prompts_dir).

        Returns:
            A string containing the generated prompt.
        """
        if not technologies:
            logger.warning("No technologies provided for prompt generation.")
            # Fallback or raise an error depending on desired behavior
            technologies = [] # Ensure it's an iterable

        all_best_practices_names: List[str] = []
        all_tools_names: List[str] = []

        for tech in technologies:
            all_best_practices_names.extend(self.knowledge_manager.get_best_practices(tech))
            all_tools_names.extend(self.knowledge_manager.get_tools(tech))

        # Get detailed information for best practices and tools, ensuring uniqueness and sorting
        detailed_best_practices: List[str] = []
        for bp_name in sorted(list(set(all_best_practices_names))):
            details = self.knowledge_manager.get_best_practice_details(bp_name)
            if details:
                detailed_best_practices.append(f"### {bp_name}\n{details}")
            else:
                detailed_best_practices.append(bp_name)  # Fallback to just name if details not found

        detailed_tools: List[str] = []
        for tool_name in sorted(list(set(all_tools_names))):
            details = self.knowledge_manager.get_tool_details(tool_name)
            if details:
                tool_info = f"### {details.get('name', tool_name)}\n"
                if details.get('description'):
                    tool_info += f"Description: {details['description']}\n"
                if details.get('benefits'):
                    tool_info += f"Benefits: {', '.join(details['benefits'])}\n"
                if details.get('usage_notes'):
                    tool_info += f"Usage Notes: {', '.join(details['usage_notes'])}\n"
                if details.get('example_command'):
                    tool_info += f"Example Command: `{details['example_command']}`\n"
                detailed_tools.append(tool_info.strip())
            else:
                detailed_tools.append(tool_name)  # Fallback to just name if details not found

        try:
            template = self.env.get_template(template_name)
        except Exception as e:
            logger.error(f"Error loading template {template_name}: {e}")
            # Fallback to a generic template or raise a specific error
            template = self.env.get_template("base_prompts/generic_code_prompt.txt")

        # Render the template with all collected information
        return template.render(
            technologies=", ".join(technologies), # Pass technologies as a comma-separated string
            task_type=task_type,
            task_description=task_description,
            best_practices="\n\n".join(detailed_best_practices),
            tools="\n\n".join(detailed_tools),
            code_requirements=code_requirements,
        )