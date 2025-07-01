import logging
from typing import Any, Dict, List, Optional, Callable
from jinja2 import Environment, FileSystemLoader
from src.knowledge_manager import KnowledgeManager
from src.prompt_config import PromptConfig

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

    def generate_prompt(self, config: PromptConfig) -> str:
        """
        Generates a formatted prompt string based on the provided configuration.
        
        Business Context: Creates contextual prompts for LLM-based code generation
        by incorporating relevant best practices and tooling information.
        
        Why this approach: Separating concerns into smaller methods improves
        testability, readability, and maintainability while reducing complexity.

        Args:
            config: Configuration object containing all prompt parameters.

        Returns:
            A string containing the generated prompt.
        """
        logger.info(f"Generating prompt for technologies: {config.technologies}")
        
        tech_data = self._collect_technology_data(config.technologies)
        template_context = self._build_template_context(config, tech_data)
        
        return self._render_template(config.template_name, template_context)
    
    def _collect_technology_data(self, technologies: List[str]) -> Dict[str, List[str]]:
        """
        Collects best practices and tools for the specified technologies.
        
        Args:
            technologies: List of technology names.
            
        Returns:
            Dictionary with 'best_practices' and 'tools' lists.
        """
        all_best_practices_names: List[str] = []
        all_tools_names: List[str] = []

        for tech in technologies:
            all_best_practices_names.extend(self.knowledge_manager.get_best_practices(tech))
            all_tools_names.extend(self.knowledge_manager.get_tools(tech))

        return {
            'best_practices': sorted(list(set(all_best_practices_names))),
            'tools': sorted(list(set(all_tools_names)))
        }
    
    def _format_knowledge_items(
        self, 
        items: List[str], 
        detail_getter: Callable[[str], Optional[Any]]
    ) -> List[str]:
        """
        Common formatting logic for best practices and tools.
        
        Eliminates code duplication between best practice and tool formatting.
        
        Args:
            items: List of item names to format.
            detail_getter: Function to retrieve details for each item.
            
        Returns:
            List of formatted item strings.
        """
        detailed_items: List[str] = []
        
        for item_name in items:
            details = detail_getter(item_name)
            if details:
                if isinstance(details, dict):
                    # Tool formatting
                    tool_info = f"### {details.get('name', item_name)}\n"
                    if details.get('description'):
                        tool_info += f"Description: {details['description']}\n"
                    if details.get('benefits'):
                        tool_info += f"Benefits: {', '.join(details['benefits'])}\n"
                    if details.get('usage_notes'):
                        tool_info += f"Usage Notes: {', '.join(details['usage_notes'])}\n"
                    if details.get('example_command'):
                        tool_info += f"Example Command: `{details['example_command']}`\n"
                    detailed_items.append(tool_info.strip())
                else:
                    # Best practice formatting (string content)
                    detailed_items.append(f"### {item_name}\n{details}")
            else:
                detailed_items.append(item_name)
                
        return detailed_items
    
    def _build_template_context(self, config: PromptConfig, tech_data: Dict[str, List[str]]) -> Dict[str, Any]:
        """
        Builds the context dictionary for template rendering.
        
        Args:
            config: Prompt configuration object.
            tech_data: Technology-specific data (best practices and tools).
            
        Returns:
            Dictionary containing all template variables.
        """
        # Format best practices
        detailed_best_practices = self._format_knowledge_items(
            tech_data['best_practices'],
            self.knowledge_manager.get_best_practice_details
        )
        
        # Format tools
        detailed_tools = self._format_knowledge_items(
            tech_data['tools'],
            self.knowledge_manager.get_tool_details
        )
        
        # Create practice details dictionary for template compatibility
        practice_details = {}
        for practice in tech_data['best_practices']:
            details = self.knowledge_manager.get_best_practice_details(practice)
            if details:
                practice_details[practice] = details
            else:
                practice_details[practice] = f'Apply enterprise {practice} standards'
        
        return {
            'technologies': config.technologies,
            'technologies_list': ", ".join(config.technologies),
            'task_type': config.task_type,
            'task_description': config.task_description,
            'best_practices': "\n\n".join(detailed_best_practices),
            'tools': "\n\n".join(detailed_tools),
            'code_requirements': config.code_requirements,
            'role': 'developer',
            # Structured data for advanced templates
            'best_practices_list': tech_data['best_practices'][:3],
            'tools_list': tech_data['tools'][:3],
            'primary_tech': config.technologies[0] if config.technologies else 'development',
            'practice_details': practice_details
        }
    
    def _render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """
        Renders the template with the provided context.
        
        Args:
            template_name: Name of the template file.
            context: Template rendering context.
            
        Returns:
            Rendered template string.
            
        Raises:
            Exception: If template loading fails and fallback also fails.
        """
        try:
            template = self.env.get_template(template_name)
        except Exception as e:
            logger.error(f"Error loading template {template_name}: {e}")
            # Fallback to generic template
            template = self.env.get_template("base_prompts/generic_code_prompt.txt")

        return template.render(**context)

    # Legacy method for backward compatibility
    def generate_prompt_legacy(
        self,
        technologies: List[str],
        task_type: str,
        code_requirements: str,
        task_description: str = "",
        template_name: str = "base_prompts/generic_code_prompt.txt",
    ) -> str:
        """
        Legacy method for backward compatibility.
        
        Args:
            technologies: A list of technologies relevant to the task.
            task_type: The general type of task.
            code_requirements: Specific requirements for the generated code.
            task_description: A detailed description of the task.
            template_name: The name of the Jinja2 template to use.

        Returns:
            A string containing the generated prompt.
        """
        config = PromptConfig(
            technologies=technologies,
            task_type=task_type,
            code_requirements=code_requirements,
            task_description=task_description,
            template_name=template_name
        )
        return self.generate_prompt(config)