import pytest
import os
import json
import src.utils
from src.knowledge_manager import KnowledgeManager
from src.utils import safe_path_join

# Setup for tests
@pytest.fixture
def setup_knowledge_base(tmp_path, mocker):
    # Create dummy config file
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    config_file = config_dir / "tech_stack_mapping.json"
    config_data = {
        "python": {"best_practices": ["PEP8"], "tools": ["Pylint"]},
        "javascript": {"best_practices": ["ESLint Recommended"], "tools": ["Jest"]},
        "docker": {"best_practices": ["Docker Best Practices"], "tools": ["Docker"]}
    }
    with open(config_file, 'w') as f:
        json.dump(config_data, f)

    # Create dummy knowledge base files
    kb_bp_dir = tmp_path / "knowledge_base" / "best_practices"
    kb_bp_dir.mkdir(parents=True)
    (kb_bp_dir / "pep8.md").write_text("PEP8 details")
    (kb_bp_dir / "docker_best_practices.md").write_text("Docker BP details")

    kb_tools_dir = tmp_path / "knowledge_base" / "tools"
    kb_tools_dir.mkdir(parents=True)
    with open(kb_tools_dir / "pylint.json", 'w') as f:
        json.dump({"name": "Pylint", "description": "Pylint tool"}, f)
    with open(kb_tools_dir / "docker.json", 'w') as f:
        json.dump({"name": "Docker", "description": "Docker tool"}, f)

    # Mock the internal _load_tech_stack_mapping method of KnowledgeManager
    # This allows us to control the initial state without actual file I/O during __init__
    mocker.patch.object(KnowledgeManager, '_load_tech_stack_mapping', return_value=config_data)

    # Mock the underlying file read functions to count calls for caching test
    mock_read_text_file = mocker.patch('src.utils.read_text_file')
    mock_load_json_file = mocker.patch('src.utils.load_json_file')

    # Configure mocks to return dummy data when called
    mock_read_text_file.side_effect = lambda path: "PEP8 details" if "pep8.md" in path else "Docker BP details"
    mock_load_json_file.side_effect = lambda path: {"name": "Pylint", "description": "Pylint tool"} if "pylint.json" in path else {"name": "Docker", "description": "Docker tool"}

    # Instantiate KnowledgeManager after mocks are set up
    km = KnowledgeManager(str(config_file), base_path=str(tmp_path))

    return km, mock_read_text_file, mock_load_json_file

def test_knowledge_manager_init(setup_knowledge_base):
    km, _, _ = setup_knowledge_base
    assert km.tech_stack_mapping is not None
    assert "python" in km.tech_stack_mapping

def test_get_best_practices(setup_knowledge_base):
    km, _, _ = setup_knowledge_base
    assert km.get_best_practices("python") == ["PEP8"]
    assert km.get_best_practices("non_existent") == []

def test_get_tools(setup_knowledge_base):
    km, _, _ = setup_knowledge_base
    assert km.get_tools("python") == ["Pylint"]
    assert km.get_tools("non_existent") == []

def test_get_best_practice_details(setup_knowledge_base):
    km, _, _ = setup_knowledge_base
    assert km.get_best_practice_details("PEP8") == "PEP8 details"
    assert km.get_best_practice_details("Non Existent BP") is None

def test_get_tool_details(setup_knowledge_base):
    km, _, _ = setup_knowledge_base
    details = km.get_tool_details("Pylint")
    assert details["name"] == "Pylint"
    assert details["description"] == "Pylint tool"
    assert km.get_tool_details("Non Existent Tool") is None

def test_knowledge_manager_caching(setup_knowledge_base):
    km, mock_read_text_file, mock_load_json_file = setup_knowledge_base

    # First call for best practice - should read from file
    km.get_best_practice_details("PEP8")
    mock_read_text_file.assert_called_once()
    mock_read_text_file.reset_mock()

    # Second call for best practice - should be from cache
    km.get_best_practice_details("PEP8")
    mock_read_text_file.assert_not_called()

    # First call for tool - should read from file
    km.get_tool_details("Pylint")
    mock_load_json_file.assert_called_once()
    mock_load_json_file.reset_mock()

    # Second call for tool - should be from cache
    km.get_tool_details("Pylint")
    mock_load_json_file.assert_not_called()

def test_safe_path_join_prevention(tmp_path):
    base_dir = str(tmp_path)
    # Attempt to traverse outside base_dir
    with pytest.raises(ValueError, match="Attempted directory traversal"):
        safe_path_join(base_dir, "..", "outside_dir")

    # Valid path within base_dir
    valid_path = safe_path_join(base_dir, "subdir", "file.txt")
    assert valid_path.startswith(os.path.abspath(base_dir))
    assert ".." not in valid_path # Ensure no '..' in normalized path