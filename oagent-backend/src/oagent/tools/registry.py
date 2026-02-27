"""Tool registry for LangChain tools."""

from typing import Dict, List, Optional, Any, Callable
import ast
import operator
from langchain_core.tools import BaseTool, tool
from loguru import logger


# Safe math operators for AST-based calculator
SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
    ast.Mod: operator.mod,
}


def _safe_eval_math(expr: str) -> float:
    """Safely evaluate mathematical expressions using AST.

    Args:
        expr: Mathematical expression string

    Returns:
        Result of evaluation

    Raises:
        ValueError: If expression contains unsafe operations
    """
    def _eval_node(node: ast.AST) -> float:
        if isinstance(node, ast.Num):  # Python 3.7
            return node.n
        if isinstance(node, ast.Constant):  # Python 3.8+
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError("Only numeric constants allowed")
        elif isinstance(node, ast.BinOp):
            left = _eval_node(node.left)
            right = _eval_node(node.right)
            op_type = type(node.op)
            if op_type not in SAFE_OPERATORS:
                raise ValueError(f"Unsafe operator: {op_type}")
            return SAFE_OPERATORS[op_type](left, right)
        elif isinstance(node, ast.UnaryOp):
            operand = _eval_node(node.operand)
            op_type = type(node.op)
            if op_type not in SAFE_OPERATORS:
                raise ValueError(f"Unsafe operator: {op_type}")
            return SAFE_OPERATORS[op_type](operand)
        else:
            raise ValueError(f"Unsupported node type: {type(node)}")

    try:
        tree = ast.parse(expr, mode='eval')
        return _eval_node(tree.body)
    except Exception as e:
        raise ValueError(f"Invalid expression: {e}")


class ToolRegistry:
    """Central registry for LangChain tools."""

    _instance: Optional["ToolRegistry"] = None

    def __new__(cls) -> "ToolRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tools: Dict[str, BaseTool] = {}
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._initialize_builtin_tools()
            self._initialized = True

    def _initialize_builtin_tools(self) -> None:
        """Initialize built-in tools."""
        tools = self._get_builtin_tools()
        for name, tool_instance in tools.items():
            self._tools[name] = tool_instance
            logger.info(f"Registered built-in tool: {name}")

    def _get_builtin_tools(self) -> Dict[str, BaseTool]:
        """Get built-in tool definitions."""

        @tool
        def calculator(expression: str) -> str:
            """Evaluate mathematical expressions safely.

            Use this when you need to perform mathematical calculations.
            Supports: +, -, *, /, ^, %, negative numbers, parentheses.
            Input should be a valid mathematical expression like "2 + 2" or "(3 * 4) / 2".
            """
            try:
                result = _safe_eval_math(expression)
                return str(result)
            except ValueError as e:
                return f"Error: {e}"
            except Exception as e:
                return f"Unexpected error: {e}"

        @tool
        def search(query: str) -> str:
            """Search the web for information.

            Use this when you need to find current information,
            news, or facts that may not be in your training data.
            """
            # Placeholder - would integrate with Tavily, SerpAPI, etc.
            return f"Search results for '{query}': [This is a placeholder. Configure actual search API.]"

        return {
            "calculator": calculator,
            "search": search,
        }

    def register(self, name: str, tool_instance: BaseTool) -> None:
        """Register a tool.

        Args:
            name: Tool name
            tool_instance: LangChain BaseTool instance
        """
        self._tools[name] = tool_instance
        logger.info(f"Registered tool: {name}")

    def unregister(self, name: str) -> bool:
        """Unregister a tool.

        Args:
            name: Tool name

        Returns:
            True if unregistered
        """
        if name in self._tools:
            del self._tools[name]
            logger.info(f"Unregistered tool: {name}")
            return True
        return False

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get tool by name.

        Args:
            name: Tool name

        Returns:
            Tool instance or None
        """
        return self._tools.get(name)

    def get_tools(self, names: List[str]) -> List[BaseTool]:
        """Get multiple tools by names.

        Args:
            names: List of tool names

        Returns:
            List of tool instances
        """
        tools = []
        for name in names:
            tool_instance = self.get_tool(name)
            if tool_instance:
                tools.append(tool_instance)
            else:
                logger.warning(f"Tool not found: {name}")
        return tools

    def list_tools(self) -> Dict[str, BaseTool]:
        """List all registered tools.

        Returns:
            Dictionary of tool name -> tool instance
        """
        return self._tools.copy()

    def get_tool_names(self) -> List[str]:
        """Get list of all tool names.

        Returns:
            List of tool names
        """
        return list(self._tools.keys())


# Global registry instance
def get_tool_registry() -> ToolRegistry:
    """Get the global tool registry."""
    return ToolRegistry()
