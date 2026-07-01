from __future__ import annotations

import ast
from pathlib import Path
from collections import defaultdict


def test_duplicate_download_buttons_have_explicit_keys():
    """Evita StreamlitDuplicateElementId cuando dos descargas comparten etiqueta y archivo."""
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    tree = ast.parse(app_path.read_text(encoding="utf-8"))
    groups = defaultdict(list)

    class Visitor(ast.NodeVisitor):
        def visit_Call(self, node):
            if isinstance(node.func, ast.Attribute) and node.func.attr == "download_button":
                label = None
                file_name = None
                key = None
                if node.args and isinstance(node.args[0], ast.Constant):
                    label = node.args[0].value
                for kw in node.keywords:
                    if kw.arg == "label" and isinstance(kw.value, ast.Constant):
                        label = kw.value.value
                    elif kw.arg == "file_name" and isinstance(kw.value, ast.Constant):
                        file_name = kw.value.value
                    elif kw.arg == "key":
                        key = ast.unparse(kw.value)
                groups[(label, file_name)].append((node.lineno, key))
            self.generic_visit(node)

    Visitor().visit(tree)
    offenders = []
    for (label, file_name), records in groups.items():
        if len(records) <= 1:
            continue
        for lineno, key in records:
            if not key:
                offenders.append((lineno, label, file_name))
    assert not offenders, f"download_button duplicados sin key explícita: {offenders}"
