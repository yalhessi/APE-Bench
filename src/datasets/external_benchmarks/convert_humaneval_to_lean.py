#!/usr/bin/env python3
"""Convert HumanEval records into Lean program-synthesis tasks."""

import argparse
import ast
import copy
import inspect
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

class ConversionError(ValueError):
    """Raised when a HumanEval item cannot be converted safely."""


@dataclass(frozen=True)
class LeanTypeSpec:
    """Lean-side type information used for hidden example rendering."""

    lean_type: str
    kind: str
    children: Tuple["LeanTypeSpec", ...] = ()


UNKNOWN_TYPE_SPEC = LeanTypeSpec("α", "unknown")
DEFAULT_LEAN_REPO_URL = "https://github.com/leanprover-community/mathlib4.git"
DEFAULT_LEAN_COMMIT_HASH = "2df2f0150c275ad53cb3c90f7c98ec15a56a1a67"
DEFAULT_CODEGEN_OUTPUT = Path("inputs/humaneval/humaneval_lean_code_generation.jsonl")
DEFAULT_SPECGEN_OUTPUT = Path("inputs/humaneval/humaneval_lean_spec_generation.jsonl")


SCALAR_TYPE_MAP = {
    "int": LeanTypeSpec("Int", "int"),
    "float": LeanTypeSpec("Float", "float"),
    "bool": LeanTypeSpec("Bool", "bool"),
    "str": LeanTypeSpec("String", "string"),
    "None": LeanTypeSpec("Unit", "unit"),
}


def _wrap_type(type_expr: str) -> str:
    """Parenthesize composite Lean types when nesting them inside other types."""
    stripped = type_expr.strip()
    if not stripped:
        return stripped
    if stripped.startswith("(") and stripped.endswith(")"):
        return stripped
    if " " in stripped or "×" in stripped:
        return f"({stripped})"
    return stripped


def _annotation_name(node: ast.AST) -> Optional[str]:
    """Return the rightmost annotation name."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _parse_annotation(node: ast.AST) -> LeanTypeSpec:
    """Convert a Python type annotation into a Lean type spec."""
    if isinstance(node, ast.Name):
        spec = SCALAR_TYPE_MAP.get(node.id)
        if spec:
            return spec
        raise ConversionError(f"Unsupported scalar annotation: {node.id}")

    if isinstance(node, ast.Constant) and node.value is None:
        return SCALAR_TYPE_MAP["None"]

    if isinstance(node, ast.Subscript):
        head = _annotation_name(node.value)
        if head is None:
            raise ConversionError(f"Unsupported annotation head: {ast.dump(node.value)}")

        slice_node = node.slice
        slice_items = list(slice_node.elts) if isinstance(slice_node, ast.Tuple) else [slice_node]

        if head in {"List", "list", "Sequence", "Iterable"}:
            if len(slice_items) != 1:
                raise ConversionError(f"{head} annotations must have exactly one parameter")
            child = _parse_annotation(slice_items[0])
            return LeanTypeSpec(f"List {_wrap_type(child.lean_type)}", "list", (child,))

        if head in {"Tuple", "tuple"}:
            if not slice_items:
                raise ConversionError("Empty tuple annotations are not supported")
            children = tuple(_parse_annotation(item) for item in slice_items)
            lean_type = " × ".join(child.lean_type for child in children)
            return LeanTypeSpec(lean_type, "tuple", children)

        if head in {"Optional"}:
            if len(slice_items) != 1:
                raise ConversionError("Optional annotations must have exactly one parameter")
            child = _parse_annotation(slice_items[0])
            return LeanTypeSpec(f"Option {_wrap_type(child.lean_type)}", "option", (child,))

        if head in {"Union"}:
            if len(slice_items) != 2:
                raise ConversionError("Only binary Union annotations are supported")
            if isinstance(slice_items[0], ast.Constant) and slice_items[0].value is None:
                child = _parse_annotation(slice_items[1])
                return LeanTypeSpec(f"Option {_wrap_type(child.lean_type)}", "option", (child,))
            if isinstance(slice_items[1], ast.Constant) and slice_items[1].value is None:
                child = _parse_annotation(slice_items[0])
                return LeanTypeSpec(f"Option {_wrap_type(child.lean_type)}", "option", (child,))
            raise ConversionError("Only Optional-like Union[T, None] annotations are supported")

        if head in {"Dict", "dict"}:
            if len(slice_items) != 2:
                raise ConversionError("Dict annotations must have exactly two parameters")
            key_spec = _parse_annotation(slice_items[0])
            value_spec = _parse_annotation(slice_items[1])
            return LeanTypeSpec(
                f"List ({key_spec.lean_type} × {value_spec.lean_type})",
                "dict_list",
                (key_spec, value_spec),
            )

        if head in {"Set", "set"}:
            if len(slice_items) != 1:
                raise ConversionError("Set annotations must have exactly one parameter")
            child = _parse_annotation(slice_items[0])
            return LeanTypeSpec(f"List {_wrap_type(child.lean_type)}", "set_list", (child,))

        raise ConversionError(f"Unsupported generic annotation: {head}")

    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        left = node.left
        right = node.right
        if isinstance(left, ast.Constant) and left.value is None:
            child = _parse_annotation(right)
            return LeanTypeSpec(f"Option {_wrap_type(child.lean_type)}", "option", (child,))
        if isinstance(right, ast.Constant) and right.value is None:
            child = _parse_annotation(left)
            return LeanTypeSpec(f"Option {_wrap_type(child.lean_type)}", "option", (child,))
        raise ConversionError("Only Optional-like T | None annotations are supported")

    raise ConversionError(f"Unsupported annotation syntax: {ast.dump(node)}")


def _parse_annotation_best_effort(node: Optional[ast.AST]) -> Optional[LeanTypeSpec]:
    """Best-effort annotation parsing.

    Missing or unsupported annotations should not exclude a HumanEval task from conversion.
    In those cases we fall back to runtime example-based inference later.
    """
    if node is None:
        return None
    try:
        return _parse_annotation(node)
    except ConversionError:
        return None


def _contains_kind(spec: LeanTypeSpec, target_kind: str) -> bool:
    """Return whether a type spec recursively contains the requested encoding kind."""
    if spec.kind == target_kind:
        return True
    return any(_contains_kind(child, target_kind) for child in spec.children)


def _infer_type_spec_from_values(values: Sequence[Any]) -> LeanTypeSpec:
    """Infer a Lean type spec from observed Python values."""
    if not values:
        return UNKNOWN_TYPE_SPEC

    non_none = [value for value in values if value is not None]
    if len(non_none) != len(values):
        if not non_none:
            return SCALAR_TYPE_MAP["None"]
        child = _infer_type_spec_from_values(non_none)
        return LeanTypeSpec(f"Option {_wrap_type(child.lean_type)}", "option", (child,))

    if all(isinstance(value, bool) for value in non_none):
        return SCALAR_TYPE_MAP["bool"]

    if all(not isinstance(value, bool) and isinstance(value, (int, float)) for value in non_none):
        if any(isinstance(value, float) for value in non_none):
            return SCALAR_TYPE_MAP["float"]
        return SCALAR_TYPE_MAP["int"]

    if all(isinstance(value, str) for value in non_none):
        return SCALAR_TYPE_MAP["str"]

    if all(isinstance(value, list) for value in non_none):
        elements = [item for value in non_none for item in value]
        child = _infer_type_spec_from_values(elements) if elements else UNKNOWN_TYPE_SPEC
        return LeanTypeSpec(f"List {_wrap_type(child.lean_type)}", "list", (child,))

    if all(isinstance(value, tuple) for value in non_none):
        arities = {len(value) for value in non_none}
        if len(arities) != 1:
            raise ConversionError("Cannot infer a fixed tuple type from varying tuple arities")
        arity = next(iter(arities))
        if arity == 0:
            return SCALAR_TYPE_MAP["None"]
        children = tuple(
            _infer_type_spec_from_values([value[index] for value in non_none])
            for index in range(arity)
        )
        return LeanTypeSpec(" × ".join(child.lean_type for child in children), "tuple", children)

    if all(isinstance(value, dict) for value in non_none):
        keys = [key for value in non_none for key in value.keys()]
        mapped_values = [mapped_value for value in non_none for mapped_value in value.values()]
        key_spec = _infer_type_spec_from_values(keys) if keys else UNKNOWN_TYPE_SPEC
        value_spec = _infer_type_spec_from_values(mapped_values) if mapped_values else UNKNOWN_TYPE_SPEC
        return LeanTypeSpec(
            f"List ({key_spec.lean_type} × {value_spec.lean_type})",
            "dict_list",
            (key_spec, value_spec),
        )

    if all(isinstance(value, (set, frozenset)) for value in non_none):
        elements = [item for value in non_none for item in value]
        child = _infer_type_spec_from_values(elements) if elements else UNKNOWN_TYPE_SPEC
        return LeanTypeSpec(f"List {_wrap_type(child.lean_type)}", "set_list", (child,))

    runtime_types = ", ".join(sorted({type(value).__name__ for value in non_none}))
    raise ConversionError(f"Unsupported runtime value types for Lean rendering: {runtime_types}")


def _build_translation_contract(specs: Iterable[LeanTypeSpec]) -> str:
    """Build a user-visible representation contract."""
    specs = list(specs)
    lines = [
        "- Translate the entire visible Python program, not only a thin wrapper around the benchmark entry point.",
        "- You may adapt the Lean signature slightly if needed, but the translated entry point must remain callable on the encoded benchmark inputs.",
        "- Base type mapping: `int -> Int`, `float -> Float`, `bool -> Bool`, `str -> String`.",
        "- Python `List[T]` maps to `List T`, `Tuple[...]` maps to Lean tuples/product types, and `Optional[T]` maps to `Option T`.",
    ]

    if any(_contains_kind(spec, "dict_list") for spec in specs):
        lines.append(
            "- Python `Dict[K, V]` values are encoded as `List (K × V)` sorted by key."
        )

    if any(_contains_kind(spec, "set_list") for spec in specs):
        lines.append(
            "- Python `Set[T]` values are encoded as sorted duplicate-free `List T`."
        )

    if any(_contains_kind(spec, "unit") for spec in specs):
        lines.append("- Python `None` is encoded as Lean `Unit`, written as `()`.")

    lines.append("- Keep the translation executable and proof-friendly; avoid opaque wrappers.")
    return "\n".join(lines)


def _sort_key_for_value(value: Any, spec: LeanTypeSpec) -> Any:
    """Build a deterministic Python-side sort key for container encodings."""
    if spec.kind == "unit":
        return ()
    if spec.kind == "bool":
        if not isinstance(value, bool):
            raise ConversionError(f"Expected bool, got {type(value).__name__}")
        return int(value)
    if spec.kind == "int":
        if isinstance(value, bool) or not isinstance(value, int):
            raise ConversionError(f"Expected int, got {type(value).__name__}")
        return value
    if spec.kind == "float":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ConversionError(f"Expected float, got {type(value).__name__}")
        return float(value)
    if spec.kind == "string":
        if not isinstance(value, str):
            raise ConversionError(f"Expected string, got {type(value).__name__}")
        return value
    if spec.kind == "option":
        if value is None:
            return (0,)
        return (1, _sort_key_for_value(value, spec.children[0]))
    if spec.kind in {"list", "set_list"}:
        if not isinstance(value, (list, tuple, set, frozenset)):
            raise ConversionError(f"Expected sequence-like value, got {type(value).__name__}")
        items = value
        if isinstance(value, (set, frozenset)):
            items = sorted(value, key=lambda item: _sort_key_for_value(item, spec.children[0]))
        return tuple(_sort_key_for_value(item, spec.children[0]) for item in items)
    if spec.kind == "tuple":
        if not isinstance(value, tuple):
            raise ConversionError(f"Expected tuple, got {type(value).__name__}")
        if len(value) != len(spec.children):
            raise ConversionError("Tuple arity mismatch during sorting")
        return tuple(_sort_key_for_value(item, child) for item, child in zip(value, spec.children))
    if spec.kind == "dict_list":
        if not isinstance(value, dict):
            raise ConversionError(f"Expected dict, got {type(value).__name__}")
        key_spec, value_spec = spec.children
        return tuple(
            (
                _sort_key_for_value(key, key_spec),
                _sort_key_for_value(mapped_value, value_spec),
            )
            for key, mapped_value in sorted(
                value.items(),
                key=lambda item: _sort_key_for_value(item[0], key_spec),
            )
        )

    if spec.kind == "unknown":
        return repr(value)

    raise ConversionError(f"Unsupported sort encoding kind: {spec.kind}")


def _wrap_term(expr: str) -> str:
    """Parenthesize Lean terms when embedding them inside larger expressions."""
    stripped = expr.strip()
    if not stripped:
        return stripped
    if stripped[0] in "([{\"'":
        return stripped
    if stripped in {"true", "false", "none", "()"}:
        return stripped
    if " " in stripped or "\n" in stripped or stripped.startswith("-"):
        return f"({stripped})"
    return stripped


def _render_lean_value(value: Any, spec: LeanTypeSpec) -> str:
    """Render a Python value as a Lean expression under the requested encoding."""
    if spec.kind == "unit":
        if value is not None:
            raise ConversionError(f"Expected None/Unit, got {type(value).__name__}")
        return "()"

    if spec.kind == "bool":
        if not isinstance(value, bool):
            raise ConversionError(f"Expected bool, got {type(value).__name__}")
        return "true" if value else "false"

    if spec.kind == "int":
        if isinstance(value, bool) or not isinstance(value, int):
            raise ConversionError(f"Expected int, got {type(value).__name__}")
        return repr(value)

    if spec.kind == "float":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ConversionError(f"Expected float, got {type(value).__name__}")
        rendered = repr(float(value))
        if rendered in {"nan", "inf", "-inf"}:
            raise ConversionError(f"Non-finite float values are not supported: {rendered}")
        return rendered

    if spec.kind == "string":
        if not isinstance(value, str):
            raise ConversionError(f"Expected string, got {type(value).__name__}")
        return json.dumps(value, ensure_ascii=False)

    if spec.kind == "option":
        if value is None:
            return "none"
        child_rendered = _render_lean_value(value, spec.children[0])
        return f"some {_wrap_term(child_rendered)}"

    if spec.kind == "list":
        if not isinstance(value, (list, tuple)):
            raise ConversionError(f"Expected list-like value, got {type(value).__name__}")
        child_spec = spec.children[0]
        rendered_items = [_render_lean_value(item, child_spec) for item in value]
        return "[" + ", ".join(rendered_items) + "]"

    if spec.kind == "tuple":
        if not isinstance(value, tuple):
            raise ConversionError(f"Expected tuple, got {type(value).__name__}")
        if len(value) != len(spec.children):
            raise ConversionError("Tuple arity mismatch during Lean rendering")
        rendered_items = [
            _render_lean_value(item, child_spec)
            for item, child_spec in zip(value, spec.children)
        ]
        return "(" + ", ".join(rendered_items) + ")"

    if spec.kind == "dict_list":
        if not isinstance(value, dict):
            raise ConversionError(f"Expected dict, got {type(value).__name__}")
        key_spec, value_spec = spec.children
        rendered_items = []
        for key, mapped_value in sorted(
            value.items(),
            key=lambda item: _sort_key_for_value(item[0], key_spec),
        ):
            key_term = _render_lean_value(key, key_spec)
            value_term = _render_lean_value(mapped_value, value_spec)
            rendered_items.append(f"({_wrap_term(key_term)}, {_wrap_term(value_term)})")
        return "[" + ", ".join(rendered_items) + "]"

    if spec.kind == "set_list":
        if not isinstance(value, (set, frozenset)):
            raise ConversionError(f"Expected set, got {type(value).__name__}")
        child_spec = spec.children[0]
        rendered_items = [
            _render_lean_value(item, child_spec)
            for item in sorted(value, key=lambda item: _sort_key_for_value(item, child_spec))
        ]
        return "[" + ", ".join(rendered_items) + "]"

    if spec.kind == "unknown":
        raise ConversionError(f"Cannot render value with unknown Lean type: {value!r}")

    raise ConversionError(f"Unsupported Lean rendering kind: {spec.kind}")


def _extract_function(record_prompt: str, entry_point: str) -> ast.FunctionDef:
    """Extract the entry-point function definition from a HumanEval prompt."""
    prompt_module = ast.parse(record_prompt)
    for node in prompt_module.body:
        if isinstance(node, ast.FunctionDef) and node.name == entry_point:
            return node
    raise ConversionError(f"Prompt does not define entry point `{entry_point}`")


def _build_signatures(
    func_def: ast.FunctionDef,
) -> Tuple[List[Tuple[str, Optional[LeanTypeSpec]]], Optional[LeanTypeSpec], str]:
    """Create best-effort signature metadata from the prompt AST."""
    if func_def.args.posonlyargs or func_def.args.kwonlyargs:
        raise ConversionError("Only standard positional arguments are supported")
    if func_def.args.vararg or func_def.args.kwarg:
        raise ConversionError("Variadic HumanEval signatures are not supported")

    arg_specs: List[Tuple[str, Optional[LeanTypeSpec]]] = []
    for arg in func_def.args.args:
        arg_specs.append((arg.arg, _parse_annotation_best_effort(arg.annotation)))

    return_spec = _parse_annotation_best_effort(func_def.returns)

    python_signature = next(
        (line.strip() for line in ast.unparse(func_def).splitlines() if line.strip().startswith("def ")),
        f"def {func_def.name}(...)",
    )
    return arg_specs, return_spec, python_signature


def _collect_examples(
    source_program: str,
    test_code: str,
    entry_point: str,
    arg_names: Sequence[str],
) -> List[Tuple[List[Any], Any]]:
    """Execute the HumanEval tests on the canonical solution and collect raw examples."""
    namespace: Dict[str, Any] = {}
    execution_program = source_program
    if "from __future__ import annotations" not in source_program:
        execution_program = "from __future__ import annotations\n" + source_program
    exec(execution_program, namespace, namespace)

    if entry_point not in namespace or not callable(namespace[entry_point]):
        raise ConversionError(f"Canonical source does not define callable `{entry_point}`")

    original_candidate = namespace[entry_point]
    signature = inspect.signature(original_candidate)

    raw_examples: List[Tuple[List[Any], Any]] = []

    def instrumented(*args, **kwargs):
        bound = signature.bind(*args, **kwargs)
        bound.apply_defaults()
        ordered_args = [
            copy.deepcopy(bound.arguments[name])
            for name in arg_names
        ]
        result = original_candidate(*args, **kwargs)
        raw_examples.append((ordered_args, copy.deepcopy(result)))
        return result

    test_namespace = dict(namespace)
    test_namespace["candidate"] = instrumented
    test_namespace[entry_point] = instrumented
    exec(test_code, test_namespace, test_namespace)

    if "check" in test_namespace and callable(test_namespace["check"]):
        test_namespace["check"](instrumented)
    elif "test_check" in test_namespace and callable(test_namespace["test_check"]):
        test_namespace["test_check"]()
    else:
        raise ConversionError("HumanEval test code did not expose check() or test_check()")

    if not raw_examples:
        raise ConversionError("No hidden examples were collected from the HumanEval tests")

    return raw_examples


def _can_render_all_values(values: Sequence[Any], spec: LeanTypeSpec) -> bool:
    """Return whether the given spec can render all observed values."""
    try:
        for value in values:
            _render_lean_value(value, spec)
        return True
    except ConversionError:
        return False


def _resolve_type_spec(
    annotation_spec: Optional[LeanTypeSpec],
    observed_values: Sequence[Any],
) -> LeanTypeSpec:
    """Choose between a parsed annotation and runtime inference."""
    if annotation_spec is not None and _can_render_all_values(observed_values, annotation_spec):
        return annotation_spec
    return _infer_type_spec_from_values(observed_values)


def _render_hidden_examples(
    raw_examples: Sequence[Tuple[List[Any], Any]],
    arg_specs: Sequence[Tuple[str, LeanTypeSpec]],
    return_spec: LeanTypeSpec,
    max_examples_per_task: Optional[int],
) -> List[Dict[str, Any]]:
    """Render raw Python examples into Lean expressions using resolved type specs."""

    hidden_examples: List[Dict[str, Any]] = []
    seen_examples = set()

    for ordered_args, expected_value in raw_examples:
        if len(ordered_args) != len(arg_specs):
            raise ConversionError("Argument count mismatch while collecting hidden examples")

        rendered_args = [
            _render_lean_value(arg_value, arg_spec)
            for arg_value, (_, arg_spec) in zip(ordered_args, arg_specs)
        ]
        rendered_expected = _render_lean_value(expected_value, return_spec)
        dedupe_key = json.dumps(
            {"args": rendered_args, "expected": rendered_expected},
            ensure_ascii=False,
            sort_keys=True,
        )
        if dedupe_key in seen_examples:
            continue

        seen_examples.add(dedupe_key)
        hidden_examples.append(
            {
                "args": rendered_args,
                "expected": rendered_expected,
            }
        )

        if max_examples_per_task is not None and len(hidden_examples) >= max_examples_per_task:
            break

    return hidden_examples


def _build_task_description(
    func_def: ast.FunctionDef,
    benchmark_task_id: str,
    task_type: str,
) -> str:
    """Create the visible task description shown to the agent."""
    if task_type == "lean_spec_generation":
        description = (
            "Formalize the provided HumanEval prompt into Lean 4 using only the prompt-level "
            "information. The canonical Python solution is intentionally hidden."
        )
    else:
        description = (
            "Translate the entire provided canonical Python program into Lean 4 so it "
            "preserves the same behavior under the requested type encoding."
        )
    docstring = inspect.cleandoc(ast.get_docstring(func_def) or "")
    if docstring:
        description += (
            f"\n\nOriginal HumanEval problem statement for `{benchmark_task_id}`:\n{docstring}"
        )
    return description


def _visible_source_program(prompt: str, canonical_solution: str, task_type: str) -> str:
    """Return the source text visible to the agent for the chosen task type."""
    if task_type == "lean_spec_generation":
        return prompt
    return prompt + canonical_solution


def _task_id_prefix(task_type: str) -> str:
    """Return the task-id prefix for the given task type."""
    if task_type == "lean_spec_generation":
        return "humaneval_spec"
    return "humaneval"


def _task_source_dir(task_type: str) -> str:
    """Return the scratch subdirectory for visible source files."""
    if task_type == "lean_spec_generation":
        return "humaneval_prompt"
    return "humaneval"


def _task_target_dir(task_type: str) -> str:
    """Return the scratch subdirectory for Lean outputs."""
    if task_type == "lean_spec_generation":
        return "humaneval_prompt"
    return "humaneval"


def convert_record(
    record: Dict[str, Any],
    *,
    repo_url: str,
    commit_hash: str,
    default_target: Optional[str],
    toolchain: Optional[str],
    max_examples_per_task: Optional[int],
    task_type: str = "lean_code_generation",
) -> Dict[str, Any]:
    """Convert a single HumanEval item into a Lean program-synthesis record."""
    from ..taxonomy.lean_task_taxonomy import annotate_record_metadata

    benchmark_task_id = record["task_id"]
    entry_point = record["entry_point"]
    prompt = record["prompt"]
    canonical_solution = record["canonical_solution"]
    test_code = record["test"]

    execution_source_program = prompt + canonical_solution
    visible_source_program = _visible_source_program(prompt, canonical_solution, task_type)
    func_def = _extract_function(prompt, entry_point)
    arg_hints, return_hint, python_signature = _build_signatures(func_def)
    raw_examples = _collect_examples(
        source_program=execution_source_program,
        test_code=test_code,
        entry_point=entry_point,
        arg_names=[name for name, _ in arg_hints],
    )

    resolved_arg_specs: List[Tuple[str, LeanTypeSpec]] = []
    for arg_index, (arg_name, arg_hint) in enumerate(arg_hints):
        observed_values = [ordered_args[arg_index] for ordered_args, _ in raw_examples]
        resolved_arg_specs.append(
            (arg_name, _resolve_type_spec(arg_hint, observed_values))
        )

    resolved_return_spec = _resolve_type_spec(
        return_hint,
        [expected_value for _, expected_value in raw_examples],
    )

    all_specs = [spec for _, spec in resolved_arg_specs] + [resolved_return_spec]
    translation_contract = _build_translation_contract(all_specs)
    hidden_examples = _render_hidden_examples(
        raw_examples=raw_examples,
        arg_specs=resolved_arg_specs,
        return_spec=resolved_return_spec,
        max_examples_per_task=max_examples_per_task,
    )

    task_slug = benchmark_task_id.replace("/", "_")
    converted = {
        "task_type": task_type,
        "task_id": f"{_task_id_prefix(task_type)}_{task_slug}",
        "task_description": _build_task_description(func_def, benchmark_task_id, task_type),
        "source_language": "python",
        "source_code": visible_source_program,
        "entry_point": entry_point,
        "translation_contract": translation_contract,
        "source_filename": f"{_task_source_dir(task_type)}/{task_slug}.py",
        "target_filename": f"{_task_target_dir(task_type)}/{task_slug}.lean",
        "benchmark_name": "HumanEval",
        "benchmark_task_id": benchmark_task_id,
        "evaluation_examples": hidden_examples,
        "target_workspace": {
            "name": "target",
            "repo_url": repo_url,
            "commit_hash": commit_hash,
            "default_target": default_target,
            "toolchain": toolchain,
            "read_only_path_patterns": ["**/*"],
        },
        "metadata": {
            "dataset": "HumanEval",
            "source_language": "python",
            "benchmark_name": "HumanEval",
            "benchmark_task_id": benchmark_task_id,
            "entry_point": entry_point,
            "python_signature": python_signature,
            "hidden_example_count": len(hidden_examples),
            "type_inference_used": any(spec is None for _, spec in arg_hints) or return_hint is None,
            "canonical_solution_visible": task_type == "lean_code_generation",
            "source_mode": "prompt_only" if task_type == "lean_spec_generation" else "full_program",
        },
    }

    annotate_record_metadata(converted)
    return converted


def _load_records(input_file: Optional[Path], dataset_name: str, split: str) -> List[Dict[str, Any]]:
    """Load HumanEval records from either a local JSONL file or Hugging Face."""
    if input_file is not None:
        records: List[Dict[str, Any]] = []
        with open(input_file, "r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        return records

    try:
        from datasets import load_dataset
    except ImportError as exc:
        raise RuntimeError(
            "datasets is required to load HumanEval from Hugging Face. "
            "Install it or provide --input-file."
        ) from exc

    dataset = load_dataset(dataset_name, split=split)
    return [dict(item) for item in dataset]


def convert_humaneval(
    *,
    input_file: Optional[Path],
    output_file: Path,
    dataset_name: str,
    split: str,
    repo_url: str,
    commit_hash: str,
    default_target: Optional[str],
    toolchain: Optional[str],
    max_examples_per_task: Optional[int],
    max_tasks: Optional[int],
    task_type: str = "lean_code_generation",
) -> Tuple[int, int]:
    """Convert a HumanEval source into Lean program-synthesis records."""
    records = _load_records(input_file=input_file, dataset_name=dataset_name, split=split)
    if max_tasks is not None:
        records = records[:max_tasks]

    output_file.parent.mkdir(parents=True, exist_ok=True)

    converted_count = 0
    error_count = 0

    with open(output_file, "w", encoding="utf-8") as handle:
        for index, record in enumerate(records, start=1):
            try:
                converted = convert_record(
                    record,
                    repo_url=repo_url,
                    commit_hash=commit_hash,
                    default_target=default_target,
                    toolchain=toolchain,
                    max_examples_per_task=max_examples_per_task,
                    task_type=task_type,
                )
                json.dump(converted, handle, ensure_ascii=False)
                handle.write("\n")
                converted_count += 1
            except Exception as exc:
                task_id = record.get("task_id", f"record_{index}")
                print(f"[skip] {task_id}: {exc}")
                error_count += 1

    return converted_count, error_count


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Convert HumanEval records into Lean program-synthesis tasks.",
    )
    parser.add_argument(
        "--input-file",
        type=Path,
        default=None,
        help="Optional local HumanEval JSONL file. If omitted, Hugging Face datasets will be used.",
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        default=None,
        help="Output JSONL file for converted tasks. If omitted, a task-type-specific default is used.",
    )
    parser.add_argument(
        "--dataset-name",
        type=str,
        default="openai/openai_humaneval",
        help="Hugging Face dataset name to load when --input-file is not provided.",
    )
    parser.add_argument(
        "--split",
        type=str,
        default="test",
        help="Dataset split to load from Hugging Face.",
    )
    parser.add_argument(
        "--repo-url",
        type=str,
        default=DEFAULT_LEAN_REPO_URL,
        help="Lean workspace repository URL used for verification.",
    )
    parser.add_argument(
        "--commit-hash",
        type=str,
        default=DEFAULT_LEAN_COMMIT_HASH,
        help="Lean workspace commit hash used for verification.",
    )
    parser.add_argument(
        "--default-target",
        type=str,
        default="Mathlib",
        help="Workspace default target directory stored in target_workspace.",
    )
    parser.add_argument(
        "--toolchain",
        type=str,
        default=None,
        help="Optional Lean toolchain override stored in target_workspace.",
    )
    parser.add_argument(
        "--max-examples-per-task",
        type=int,
        default=64,
        help="Maximum number of hidden examples to retain per task.",
    )
    parser.add_argument(
        "--max-tasks",
        type=int,
        default=None,
        help="Optional cap on the number of HumanEval tasks to convert.",
    )
    parser.add_argument(
        "--task-type",
        type=str,
        choices=["lean_code_generation", "lean_spec_generation"],
        default="lean_code_generation",
        help="Type of Lean task to emit: full-program translation or prompt-only formalization.",
    )

    args = parser.parse_args()

    output_file = args.output_file
    if output_file is None:
        output_file = (
            DEFAULT_SPECGEN_OUTPUT
            if args.task_type == "lean_spec_generation"
            else DEFAULT_CODEGEN_OUTPUT
        )

    converted_count, error_count = convert_humaneval(
        input_file=args.input_file,
        output_file=output_file,
        dataset_name=args.dataset_name,
        split=args.split,
        repo_url=args.repo_url,
        commit_hash=args.commit_hash,
        default_target=args.default_target,
        toolchain=args.toolchain,
        max_examples_per_task=args.max_examples_per_task,
        max_tasks=args.max_tasks,
        task_type=args.task_type,
    )

    print(f"Converted {converted_count} tasks with {error_count} skips.")
    print(f"Output written to: {output_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
