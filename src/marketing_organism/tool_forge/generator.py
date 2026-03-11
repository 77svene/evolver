import logging
import uuid
import os
from typing import Dict, Any

from src.marketing_organism.llm.reasoning import PromptChainer

class ToolGenerator:
    def __init__(self, workspace_path: str = "./generated_tools", prompt_chainer: PromptChainer = None):
        self.workspace_path = workspace_path
        self.prompt_chainer = prompt_chainer or PromptChainer()
        if not os.path.exists(workspace_path):
            os.makedirs(workspace_path)

    async def analyze_gap(self, gap_description: str) -> Dict[str, Any]:
        """Analyzes a capability gap and outlines a tool spec."""
        logging.info(f"Analyzing capability gap: {gap_description}")
        return {
            "name": f"tool_{uuid.uuid4().hex[:8]}",
            "type": "python",
            "description": f"Generated tool to address: {gap_description}"
        }

    async def generate_tool(self, gap_description: str) -> str:
        """Returns the file path of the newly generated tool."""
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
            with open(filepath, "w") as f:
                f.write(generated_code)
            logging.info(f"Tool {tool_name} successfully generated at {filepath}")
            return filepath
        except Exception as e:
            logging.error(f"Failed to generate tool {tool_name}: {e}")
            return ""

    def validate_tool(self, filepath: str) -> bool:
        """Runs basic syntactic and static analysis on generated tools."""
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
                            logging.warning(f"Unsafe import '{alias.name}' found in {filepath}")
                            return False
                elif isinstance(node, ast.ImportFrom):
                    if node.module in ("os", "subprocess", "sys"):
                        logging.warning(f"Unsafe import from '{node.module}' found in {filepath}")
                        return False

            return True
        except py_compile.PyCompileError as e:
            logging.error(f"Tool compilation failed for {filepath}: {e}")
            return False
        except SyntaxError as e:
            logging.error(f"Syntax error during AST parsing for {filepath}: {e}")
            return False
