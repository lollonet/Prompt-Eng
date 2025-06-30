from dataclasses import dataclass
from typing import List


@dataclass
class PromptConfig:
    """
    Configuration object for prompt generation.
    
    Business Context: Encapsulates all parameters needed for prompt generation
    in a single, validated object, reducing parameter counts and improving 
    maintainability.
    
    Why this approach: Using a configuration object follows the Parameter Object
    pattern, making the API cleaner and more extensible while maintaining
    type safety.
    """
    technologies: List[str]
    task_type: str
    code_requirements: str
    task_description: str = ""
    template_name: str = "base_prompts/generic_code_prompt.txt"
    
    def __post_init__(self):
        """
        Validates configuration after initialization.
        
        Raises:
            ValueError: If validation fails for any parameter.
        """
        if not self.technologies:
            raise ValueError("At least one technology must be specified")
        
        if not self.task_type or len(self.task_type.strip()) < 3:
            raise ValueError("Task type must be descriptive (minimum 3 characters)")
        
        if not self.code_requirements or len(self.code_requirements.strip()) < 10:
            raise ValueError("Code requirements must be detailed (minimum 10 characters)")
        
        # Normalize empty strings to prevent template rendering issues
        self.task_description = self.task_description.strip()
        self.task_type = self.task_type.strip()
        self.code_requirements = self.code_requirements.strip()
        
        # Validate technologies list contains only non-empty strings
        self.technologies = [tech.strip().lower() for tech in self.technologies if tech.strip()]
        if not self.technologies:
            raise ValueError("Technologies list cannot be empty after cleaning")