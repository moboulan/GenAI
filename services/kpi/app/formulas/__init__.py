from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable, Dict, Iterable, Mapping

import yaml


class FormulaError(RuntimeError):
    """Base error for formula processing."""


class FormulaNotFound(FormulaError):
    def __init__(self, name: str):
        super().__init__(f"Unknown KPI formula '{name}'")
        self.name = name


class FormulaDataUnavailable(FormulaError):
    def __init__(self, name: str, tag: str):
        super().__init__(f"No data for tag '{tag}' to compute '{name}'")
        self.name = name
        self.tag = tag


class FormulaEvaluationError(FormulaError):
    pass


@dataclass(frozen=True)
class FormulaDefinition:
    name: str
    label: str
    unit: str
    expression: str
    description: str
    required_tags: list[str]
    default_window_minutes: int = 30

    def metadata(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "label": self.label,
            "unit": self.unit,
            "description": self.description,
            "default_window_minutes": self.default_window_minutes,
            "required_tags": list(self.required_tags),
        }


def load_definitions(path: str | Path) -> list[FormulaDefinition]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    definitions: Iterable[Mapping[str, Any]] = data.get("kpis", [])
    items: list[FormulaDefinition] = []
    for item in definitions:
        required_tags = item.get("required_tags", [])
        if not required_tags:
            raise FormulaEvaluationError(f"Formula '{item.get('name')}' missing required_tags")
        items.append(
            FormulaDefinition(
                name=item["name"],
                label=item["label"],
                unit=item["unit"],
                expression=item["expression"],
                description=item.get("description", ""),
                required_tags=list(required_tags),
                default_window_minutes=int(item.get("default_window_minutes", 30)),
            )
        )
    if not items:
        raise FormulaEvaluationError("No KPI formulas defined")
    return items


class FormulaRegistry:
    def __init__(self, definitions: Dict[str, FormulaDefinition]):
        self._definitions = definitions

    @classmethod
    def from_path(cls, path: str | Path) -> "FormulaRegistry":
        defs = {definition.name: definition for definition in load_definitions(path)}
        return cls(defs)

    def list(self) -> list[FormulaDefinition]:
        return list(self._definitions.values())

    def get(self, name: str) -> FormulaDefinition:
        if name not in self._definitions:
            raise FormulaNotFound(name)
        return self._definitions[name]


ALLOWED_FUNCTIONS: dict[str, Callable[..., Any]] = {
    "min": min,
    "max": max,
    "abs": abs,
    "round": round,
}


class _SafeEvaluator(ast.NodeVisitor):
    def __init__(self, context: Mapping[str, Any]):
        self._context = context

    def visit(self, node: ast.AST) -> Any:  # type: ignore[override]
        method = "visit_" + node.__class__.__name__
        visitor = getattr(self, method, None)
        if visitor is None:
            raise FormulaEvaluationError(f"Unsupported expression node: {node.__class__.__name__}")
        return visitor(node)

    def visit_Expression(self, node: ast.Expression) -> Any:
        return self.visit(node.body)

    def visit_BinOp(self, node: ast.BinOp) -> Any:
        left = self.visit(node.left)
        right = self.visit(node.right)
        op = node.op
        if isinstance(op, ast.Add):
            return left + right
        if isinstance(op, ast.Sub):
            return left - right
        if isinstance(op, ast.Mult):
            return left * right
        if isinstance(op, ast.Div):
            return left / right
        if isinstance(op, ast.FloorDiv):
            return left // right
        if isinstance(op, ast.Mod):
            return left % right
        if isinstance(op, ast.Pow):
            return left**right
        raise FormulaEvaluationError("Unsupported binary operator")

    def visit_UnaryOp(self, node: ast.UnaryOp) -> Any:
        operand = self.visit(node.operand)
        if isinstance(node.op, ast.USub):
            return -operand
        if isinstance(node.op, ast.UAdd):
            return +operand
        raise FormulaEvaluationError("Unsupported unary operator")

    def visit_Call(self, node: ast.Call) -> Any:
        if not isinstance(node.func, ast.Name):
            raise FormulaEvaluationError("Only simple function calls are allowed")
        func_name = node.func.id
        if func_name not in ALLOWED_FUNCTIONS:
            raise FormulaEvaluationError(f"Function '{func_name}' is not allowed")
        func = ALLOWED_FUNCTIONS[func_name]
        args = [self.visit(arg) for arg in node.args]
        kwargs = {kw.arg: self.visit(kw.value) for kw in node.keywords}
        return func(*args, **kwargs)

    def visit_Name(self, node: ast.Name) -> Any:
        if node.id not in self._context:
            raise FormulaEvaluationError(f"Unknown symbol '{node.id}' in expression")
        return self._context[node.id]

    def visit_Attribute(self, node: ast.Attribute) -> Any:
        value = self.visit(node.value)
        if not hasattr(value, node.attr):
            raise FormulaEvaluationError(f"Symbol '{node.attr}' not available on '{value}'")
        return getattr(value, node.attr)

    def visit_Constant(self, node: ast.Constant) -> Any:
        return node.value

    def visit_Num(self, node: ast.Num) -> Any:  # pragma: no cover - for legacy compatibility
        return node.n

    def visit_Compare(self, node: ast.Compare) -> Any:
        left = self.visit(node.left)
        result = True
        for op, comparator in zip(node.ops, node.comparators, strict=False):
            right = self.visit(comparator)
            if isinstance(op, ast.Gt):
                result = result and left > right
            elif isinstance(op, ast.Lt):
                result = result and left < right
            elif isinstance(op, ast.GtE):
                result = result and left >= right
            elif isinstance(op, ast.LtE):
                result = result and left <= right
            elif isinstance(op, ast.Eq):
                result = result and left == right
            elif isinstance(op, ast.NotEq):
                result = result and left != right
            else:
                raise FormulaEvaluationError("Unsupported comparison operator")
            left = right
        return result

    def visit_BoolOp(self, node: ast.BoolOp) -> Any:
        if isinstance(node.op, ast.And):
            for value in node.values:
                if not self.visit(value):
                    return False
            return True
        if isinstance(node.op, ast.Or):
            for value in node.values:
                if self.visit(value):
                    return True
            return False
        raise FormulaEvaluationError("Unsupported boolean operator")

    def visit_IfExp(self, node: ast.IfExp) -> Any:
        return self.visit(node.body) if self.visit(node.test) else self.visit(node.orelse)


def evaluate_expression(expression: str, context: Mapping[str, Any]) -> Any:
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:  # pragma: no cover - validated during load
        raise FormulaEvaluationError(f"Invalid expression: {expression}") from exc
    evaluator = _SafeEvaluator(context)
    return evaluator.visit(tree)


def make_context(inputs: Mapping[str, Mapping[str, Any]]) -> Dict[str, SimpleNamespace]:
    return {name: SimpleNamespace(**values) for name, values in inputs.items()}