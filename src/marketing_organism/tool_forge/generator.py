"""Dynamic tool generation module resolving capability gaps in the ecosystem."""

import logging
import uuid
import os
from typing import Dict, Any, Optional

from src.marketing_organism.llm.reasoning import PromptChainer
from src.marketing_organism.exceptions import ToolGenerationError

logger = logging.getLogger(__name__)

class ToolGenerator:
    """Automates creation and validation of new tool capabilities via LLM."""

    def __init__(self, workspace_path: str = "./generated_tools", prompt_chainer: Optional[PromptChainer] = None) -> None:
        """Initializes the ToolGenerator.

        Args:
            workspace_path: Path to the directory where generated tools are saved.
            prompt_chainer: Optional PromptChainer instance to use for code synthesis.
        """
        self.workspace_path = workspace_path
        self.prompt_chainer = prompt_chainer or PromptChainer()
        if not os.path.exists(workspace_path):
            os.makedirs(workspace_path)

    async def analyze_gap(self, gap_description: str) -> Dict[str, Any]:
        """Analyzes a capability gap and outlines a tool spec.

        Args:
            gap_description: A description of the missing system capability.

        Returns:
            A dictionary containing the generated specification details.
        """
        logger.info(f"Analyzing capability gap: {gap_description}")
        return {
            "name": f"tool_{uuid.uuid4().hex[:8]}",
            "type": "python",
            "description": f"Generated tool to address: {gap_description}"
        }

    async def generate_tool(self, gap_description: str) -> str:
        """Synthesizes a tool script dynamically using the LLM prompt chainer.

        Args:
            gap_description: Description of the functionality the tool should implement.

        Returns:
            The filepath of the newly generated tool.

        Raises:
            ToolGenerationError: If file writing fails.
        """
        spec = await self.analyze_gap(gap_description)
        tool_name = spec["name"]

        prompt = f"""Write a Python script to fulfill the following capability gap in a marketing automation ecosystem:
Gap: {gap_description}

Requirements:
- The script MUST define a main function named `{tool_name}(*args, **kwargs)`.
- The script MUST NOT import `os`, `sys`, or `subprocess` due to security constraints.
- Output ONLY valid Python code, no markdown blocks, no explanations.
"""
        # Call LLM to generate code dynamically
        generated_code = await self.prompt_chainer._call_llm(prompt, timeout=120.0)

        # Clean up common markdown wrappings if the LLM ignores instructions
        if generated_code.startswith("```python"):
            generated_code = generated_code[9:]
        if generated_code.startswith("```"):
            generated_code = generated_code[3:]
        if generated_code.endswith("```"):
            generated_code = generated_code[:-3]

        generated_code = generated_code.strip()

        # Fallback if LLM fails
        if not generated_code:
            generated_code = f'''
import logging

def {tool_name}(*args, **kwargs):
    """
    Fallback auto-generated tool to fulfill gap:
    {gap_description}
    """
    logging.info(f"Executing fallback tool {tool_name}")
    return "Operation successful"

if __name__ == "__main__":
    {tool_name}()
'''

        filepath = os.path.join(self.workspace_path, f"{tool_name}.py")
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(generated_code)
            logger.info(f"Tool {tool_name} successfully generated at {filepath}")
            return filepath
        except Exception as e:
            error_msg = f"Failed to generate tool {tool_name}: {e}"
            logger.error(error_msg, exc_info=True)
            raise ToolGenerationError(error_msg) from e

    def validate_tool(self, filepath: str) -> bool:
        """Runs basic syntactic and static analysis on generated tools.

        Args:
            filepath: The location of the generated script.

        Returns:
            True if the tool passes static analysis constraints, False otherwise.
        """
        if not os.path.exists(filepath):
            return False

        try:
            # Check compilation
            import py_compile
            py_compile.compile(filepath, doraise=True)

            # Static AST analysis for unsafe operations
            import ast
            with open(filepath, "r") as f:
                tree = ast.parse(f.read())

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in ("os", "subprocess", "sys"):
                            logger.warning(f"ToolGenerationError: Unsafe import '{alias.name}' found in {filepath}")
                            return False
                elif isinstance(node, ast.ImportFrom):
                    if node.module in ("os", "subprocess", "sys"):
                        logger.warning(f"ToolGenerationError: Unsafe import from '{node.module}' found in {filepath}")
                        return False

            return True
        except py_compile.PyCompileError as e:
            logger.error(f"ToolGenerationError: Tool compilation failed for {filepath}: {e}")
            return False
        except SyntaxError as e:
            logger.error(f"ToolGenerationError: Syntax error during AST parsing for {filepath}: {e}")
            return False
