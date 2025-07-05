import argparse
from pathlib import Path

import structlog
from jinja2 import Environment, FileSystemLoader
from poethepoet.app import PoeThePoet  # pyright: ignore[reportMissingTypeStubs]

log: structlog.BoundLogger = structlog.get_logger()


def add_package(args: argparse.Namespace):
    """Creates a new package with the given name."""
    package_name = args.name

    env = Environment(loader=FileSystemLoader(str(Path(__file__).parent / "templates")))

    # Create package directory
    package_dir = Path(f"todo_api/{package_name}")
    package_dir.mkdir(exist_ok=True)

    for template_name in env.list_templates(filter_func=lambda x: not x.startswith("test_")):
        template = env.get_template(template_name)
        content = template.render(package_name=package_name)
        file_name = template_name.replace(".j2", "")
        (package_dir / file_name).write_text(content)

    log.info(f"Package {package_name} created successfully.")

    # Create test directory
    test_dir = Path(f"tests/{package_name}s")
    test_dir.mkdir(exist_ok=True)
    (test_dir / "__init__.py").touch()

    template = env.get_template("test_router.py.j2")
    content = template.render(package_name=package_name)
    (test_dir / "test_router.py").write_text(content)

    log.info(f"Tests for {package_name} created successfully.")

    # Modify api.py to include the new router
    api_py_path = Path("todo_api/api.py")
    content = api_py_path.read_text()

    # Add import statement before the router_v1 definition
    import_statement = (
        f"from todo_api.{package_name}.router import router as {package_name}_router"
    )
    content = content.replace(
        'router_v1 = APIRouter(prefix="/v1")',
        f'{import_statement}\n\nrouter_v1 = APIRouter(prefix="/v1")',
    )

    # Add include_router statement to the end of the file
    include_statement = f"router_v1.include_router({package_name}_router)"
    content += f"{include_statement}\n"

    api_py_path.write_text(content)
    log.info(f"Router for {package_name} added to todo_api/api.py.")

    # Add import to migrations/env.py
    env_py_path = Path("migrations/env.py")
    env_content = env_py_path.read_text()
    import_line = f"from todo_api.{package_name}.models import *"

    target_line = "from todo_api.users.models import *"
    replacement = f"{target_line}\n{import_line}"

    if target_line in env_content:
        env_content = env_content.replace(target_line, replacement)
        log.info(f"Import for {package_name} added to migrations/env.py.")
    else:
        log.warning(
            f"Could not find target line '{target_line}' in migrations/env.py. "
            f"Import for {package_name} was not added automatically."
        )

    env_py_path.write_text(env_content)
    log.info(f"Import for {package_name} added to migrations/env.py.")

    # Run ruff format
    log.info("Running ruff format...")
    poe = PoeThePoet()
    poe(["format"])
    log.info("Ruff format complete.")


def main():
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
