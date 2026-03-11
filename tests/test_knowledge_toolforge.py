import pytest
from src.marketing_organism.knowledge.graph import KnowledgeGraph
from src.marketing_organism.tool_forge.generator import ToolGenerator
import os
import uuid

@pytest.mark.asyncio
async def test_knowledge_graph():
    kg = KnowledgeGraph(in_memory=True)
    await kg.store_entity("entity1", {"name": "Node A", "type": "campaign"})
    await kg.store_entity("entity2", {"name": "Node B", "type": "audience"})

    e1 = await kg.get_entity("entity1")
    e2 = await kg.get_entity("entity2")

    assert e1["name"] == "Node A"
    assert e2["type"] == "audience"

    await kg.add_relationship("entity1", "entity2", "targets")

    relations = await kg.query_relations("entity1")
    assert len(relations) == 1
    assert relations[0]["target"] == "entity2"
    assert relations[0]["type"] == "targets"

    campaigns = await kg.query_by_type("campaign")
    assert len(campaigns) == 1
    assert campaigns[0]["id"] == "entity1"

def test_tool_generator(tmp_path):
    generator = ToolGenerator(workspace_path=str(tmp_path))

    gap_description = "Need to parse unstructured social media text"

    # We will patch analyze_gap so the uuid generated matches during test
    original_analyze_gap = generator.analyze_gap
    def mock_analyze(gap):
        return {
            "name": f"tool_mocked123",
            "type": "python",
            "description": f"Generated tool to address: {gap}"
        }
    generator.analyze_gap = mock_analyze

    spec = generator.analyze_gap(gap_description)
    assert spec["name"].startswith("tool_")

    filepath = generator.generate_tool(gap_description)
    assert filepath.endswith(".py")
    assert os.path.exists(filepath)

    with open(filepath, "r") as f:
        content = f.read()
        assert gap_description in content
        assert spec["name"] in content

    assert generator.validate_tool(filepath) is True

    # Test AST Unsafe scanner
    unsafe_code = """
import os
def bad_tool():
    os.system("rm -rf /")
"""
    unsafe_filepath = os.path.join(generator.workspace_path, "tool_unsafe.py")
    with open(unsafe_filepath, "w") as f:
        f.write(unsafe_code)

    assert generator.validate_tool(unsafe_filepath) is False
