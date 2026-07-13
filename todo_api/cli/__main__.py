import argparse
import re
from pathlib import Path

import structlog
from jinja2 import Environment, FileSystemLoader
from poethepoet.app import PoeThePoet  # pyright: ignore[reportMissingTypeStubs]

log: structlog.BoundLogger = structlog.get_logger()


def discover_package_name() -> str:
    """Discovers the root package name by looking for main.py"""
    # `parent.parent` should be the package root
    package_path = Path(__file__).resolve().parent.parent
    return package_path.name


def add_package(args: argparse.Namespace) -> None:
    module_name = args.name
    root_package = discover_package_name()

    env = Environment(loader=FileSystemLoader(str(Path(__file__).parent / "templates")))

    # Feature packages contain HTTP-independent models and services.
    package_dir = Path(root_package) / module_name
    if package_dir.exists():
        log.error(f"Directory {package_dir} already exists.")
        return
    package_dir.mkdir(parents=True)

    api_package_dir = Path(root_package) / "api"
    api_paths = {
        "dependencies.py.j2": api_package_dir / "dependencies" / f"{module_name}.py",
        "schemas.py.j2": api_package_dir / "schemas" / f"{module_name}.py",
        "router.py.j2": api_package_dir / "routers" / f"{module_name}.py",
    }
    feature_paths = {
        "__init__.py.j2": package_dir / "__init__.py",
        "models.py.j2": package_dir / "models.py",
        "service.py.j2": package_dir / "service.py",
    }

    for template_name, output_path in {**feature_paths, **api_paths}.items():
        template = env.get_template(template_name)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            template.render(package_name=module_name, root_package=root_package)
        )

    log.info(f"Feature package {module_name} and its API adapter created successfully.")

    # Create test directory
    test_dir = Path(f"tests/{module_name}s")
    test_dir.mkdir(parents=True, exist_ok=True)
    (test_dir / "__init__.py").touch()

    template = env.get_template("test_router.py.j2")
    content = template.render(package_name=module_name, root_package=root_package)
    (test_dir / "test_router.py").write_text(content)

    log.info(f"Tests for {module_name} created successfully in {test_dir}.")

    # Register the generated HTTP router in the API adapter.
    api_py_path = Path(root_package) / "api" / "router.py"
    if api_py_path.exists():
        content = api_py_path.read_text()

        # Add import
        import_stmt = (
            f"from {root_package}.api.routers.{module_name} import router as {module_name}_router"
        )
        if import_stmt not in content:
            # Find the last import from root_package
            matches = list(
                re.finditer(rf"from {root_package}\..* import .* as .*_router", content)
            )
            if matches:
                last_match = matches[-1]
                content = (
                    content[: last_match.end()] + f"\n{import_stmt}" + content[last_match.end() :]
                )
            else:
                # Fallback: insert before router_v1 definition
                content = content.replace(
                    'router_v1 = APIRouter(prefix="/v1")',
                    f'{import_stmt}\n\nrouter_v1 = APIRouter(prefix="/v1")',
                )

        # Add include_router
        include_stmt = f"router_v1.include_router({module_name}_router)"
        if include_stmt not in content:
            # Append after last include_router
            include_matches = list(re.finditer(r"router_v1\.include_router\(.*_router\)", content))
            if include_matches:
                last_match = include_matches[-1]
                content = (
                    content[: last_match.end()] + f"\n{include_stmt}" + content[last_match.end() :]
                )
            else:
                content += f"\n{include_stmt}\n"

        api_py_path.write_text(content)
        log.info(f"Router for {module_name} added to {api_py_path}.")

    # Add import to migrations/env.py
    env_py_path = Path("migrations/env.py")
    if env_py_path.exists():
        env_content = env_py_path.read_text()
        import_line = f"from {root_package}.{module_name}.models import *"

        if import_line not in env_content:
            # Find last model import from root_package
            matches = list(re.finditer(rf"from {root_package}\..+\.models import \*", env_content))
            if matches:
                last_match = matches[-1]
                env_content = (
                    env_content[: last_match.end()]
                    + f"\n{import_line}"
                    + env_content[last_match.end() :]
                )
            else:
                # Fallback: find any models import or common target
                target_line = f"from {root_package}.users.models import *"
                if target_line in env_content:
                    env_content = env_content.replace(target_line, f"{target_line}\n{import_line}")
                else:
                    log.warning(
                        f"Could not find a suitable place to insert model import in {env_py_path}"
                    )

        env_py_path.write_text(env_content)
        log.info(f"Import for {module_name} added to {env_py_path}.")

    # Run ruff format
    log.info("Running ruff format...")
    poe = PoeThePoet()
    poe(["format"])
    log.info("Ruff format complete.")


def main() -> None:
    """Main function to run the CLI."""
    parser = argparse.ArgumentParser(prog="poe cli", description="CLI for todo_api")
    subparsers = parser.add_subparsers()

    parser_add = subparsers.add_parser("add_package", help="Add a new package")
    parser_add.add_argument("name", help="Name of the package to add")
    parser_add.set_defaults(func=add_package)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
