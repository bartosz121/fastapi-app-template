import argparse
from pathlib import Path

import structlog
from jinja2 import Environment, FileSystemLoader
from poethepoet.app import PoeThePoet

log: structlog.BoundLogger = structlog.get_logger()


def add_package(args):
    """Creates a new package with the given name."""
    package_name = args.name

    env = Environment(loader=FileSystemLoader(str(Path(__file__).parent / "templates")))

    package_dir = Path(f"todo_api/{package_name}")
    package_dir.mkdir(exist_ok=True)

    for template_name in env.list_templates():
        template = env.get_template(template_name)
        content = template.render(package_name=package_name)
        file_name = template_name.replace(".j2", "")
        (package_dir / file_name).write_text(content)

    log.info(f"Package {package_name} created successfully.")

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
