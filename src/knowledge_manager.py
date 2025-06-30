from src.utils import load_json_file
import os

class KnowledgeManager:
    def __init__(self, config_path):
        self.tech_stack_mapping = load_json_file(config_path)
        self.knowledge_base_root = os.path.dirname(os.path.dirname(config_path)) # Assumes config is in project_root/config

    def get_best_practices(self, technology):
        return self.tech_stack_mapping.get(technology, {}).get("best_practices", [])

    def get_tools(self, technology):
        return self.tech_stack_mapping.get(technology, {}).get("tools", [])

    def get_best_practice_details(self, bp_name):
        # Assuming best practice files are in knowledge_base/best_practices/ and are .md
        filepath = os.path.join(self.knowledge_base_root, "knowledge_base", "best_practices", f"{bp_name.lower().replace(' ', '_')}.md")
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                return f.read()
        return None

    def get_tool_details(self, tool_name):
        # Assuming tool files are in knowledge_base/tools/ and are .json
        filepath = os.path.join(self.knowledge_base_root, "knowledge_base", "tools", f"{tool_name.lower().replace(' ', '_')}.json")
        if os.path.exists(filepath):
            return load_json_file(filepath)
        return None
