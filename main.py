from src.prompt_generator import PromptGenerator
import os

# Define paths relative to the project root
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
PROMPTS_DIR = os.path.join(PROJECT_ROOT, "prompts")
CONFIG_PATH = os.path.join(PROJECT_ROOT, "config", "tech_stack_mapping.json")

def main():
    generator = PromptGenerator(PROMPTS_DIR, CONFIG_PATH)

    # Example usage with specific Python template
    technologies_python = ["python"]
    task_type_python = "nuova funzionalità di autenticazione"
    task_description_python = "un endpoint API per la registrazione utenti con validazione input e hashing password"
    code_requirements_python = "Il codice deve essere modulare, testabile e seguire i principi SOLID. Utilizzare un ORM per l'interazione con il database."

    generated_prompt_python = generator.generate_prompt(
        technologies=technologies_python,
        task_type=task_type_python,
        task_description=task_description_python,
        code_requirements=code_requirements_python,
        template_name="language_specific/python/feature_prompt.txt"
    )

    print("--- Generated Prompt (Python Feature) ---")
    print(generated_prompt_python)
    print("-----------------------------------------")

    # Example: JavaScript with React using specific template
    technologies_react = ["javascript", "react"]
    task_type_react = "componente UI per un form di registrazione"
    task_description_react = "un componente React per un form di login con validazione client-side"
    code_requirements_react = "Il componente deve essere riutilizzabile, accessibile e utilizzare React Hooks. Gestire lo stato del form in modo efficiente."

    generated_prompt_react = generator.generate_prompt(
        technologies=technologies_react,
        task_type=task_type_react,
        task_description=task_description_react,
        code_requirements=code_requirements_react,
        template_name="framework_specific/react/component_prompt.txt"
    )

    print("\n--- Generated Prompt (React) ---")
    print(generated_prompt_react)
    print("--------------------------------")

    # New example: Python backend with Docker, Docker Compose, and Ansible
    technologies_devops = ["python", "docker", "docker_compose", "ansible"]
    task_type_devops = "setup ambiente di sviluppo e deployment"
    task_description_devops = "un ambiente di sviluppo locale con Docker Compose e uno script Ansible per il deployment su un server remoto"
    code_requirements_devops = "L'ambiente deve essere riproducibile, facile da configurare e il deployment deve essere automatizzato e idempotente."

    generated_prompt_devops = generator.generate_prompt(
        technologies=technologies_devops,
        task_type=task_type_devops,
        task_description=task_description_devops,
        code_requirements=code_requirements_devops,
        template_name="base_prompts/generic_code_prompt.txt" # Using generic template for now
    )

    print("\n--- Generated Prompt (DevOps) ---")
    print(generated_prompt_devops)
    print("---------------------------------")

if __name__ == "__main__":
    main()