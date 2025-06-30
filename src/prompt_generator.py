from jinja2 import Environment, FileSystemLoader
from src.knowledge_manager import KnowledgeManager

class PromptGenerator:
    def __init__(self, prompts_dir, config_path):
        self.env = Environment(loader=FileSystemLoader(prompts_dir))
        self.knowledge_manager = KnowledgeManager(config_path)

    def generate_prompt(
        self,
        technologies: list[str],
        task_type: str,
        code_requirements: str,
        task_description: str = "",
        template_name: str = "base_prompts/generic_code_prompt.txt",
    ) -> str:
        all_best_practices_names = []
        all_tools_names = []

        for tech in technologies:
            all_best_practices_names.extend(self.knowledge_manager.get_best_practices(tech))
            all_tools_names.extend(self.knowledge_manager.get_tools(tech))

        # Get detailed information for best practices and tools
        detailed_best_practices = []
        for bp_name in sorted(list(set(all_best_practices_names))):
            details = self.knowledge_manager.get_best_practice_details(bp_name)
            if details:
                detailed_best_practices.append(f"### {bp_name}\n{details}")
            else:
                detailed_best_practices.append(bp_name) # Fallback to just name if details not found

        detailed_tools = []
        for tool_name in sorted(list(set(all_tools_names))):
            if tool_name == "Docker": # Special handling for Docker to avoid duplicate entry if Docker Compose is also present
                if "Docker Compose" in all_tools_names and self.knowledge_manager.get_tool_details("Docker Compose"):
                    continue # Docker details will be implicitly covered by Docker Compose

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
                detailed_tools.append(tool_name) # Fallback to just name if details not found

        template = self.env.get_template(template_name)
        return template.render(
            language=technologies[0] if technologies else "", # For backward compatibility with templates expecting 'language'
            framework=technologies[1] if len(technologies) > 1 else "", # For backward compatibility with templates expecting 'framework'
            technologies=", ".join(technologies), # New parameter for templates
            task_type=task_type,
            task_description=task_description,
            best_practices="\n\n".join(detailed_best_practices),
            tools="\n\n".join(detailed_tools),
            code_requirements=code_requirements,
        )
