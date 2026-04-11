from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def iter_python_files() -> list[Path]:
    return [
        path for path in REPO_ROOT.rglob("*.py")
        if "__pycache__" not in path.parts and ".pytest_cache" not in path.parts
    ]


def test_application_does_not_import_adapters() -> None:
    for path in iter_python_files():
        if "packages" not in path.parts or "application" not in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        assert "shadowgen_adapters" not in text, f"Application layer imports adapters in {path}"


def test_domain_does_not_import_transport_libraries() -> None:
    forbidden = ("fastapi", "httpx", "boto3", "shadowgen_adapters")
    for path in iter_python_files():
        if "packages" not in path.parts or "domain" not in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        for marker in forbidden:
            assert marker not in text, f"Domain layer imports {marker} in {path}"


def test_legacy_http_details_stay_inside_legacy_adapter() -> None:
    marker = "/v1/" + "process"
    for path in iter_python_files():
        if "legacy_pipeline" in path.parts or path.name in {"test_architecture_boundaries.py", "test_legacy_http_adapter.py"}:
            continue
        text = path.read_text(encoding="utf-8")
        assert marker not in text, f"Legacy endpoint leaked outside adapter in {path}"
