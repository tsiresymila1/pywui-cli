import os.path
import platform
import shutil
import subprocess
import sys
import typing
from subprocess import DEVNULL, check_call, run as run_cmd

import rich_click as click
import ujson
from yaspin import yaspin

from .builder import PyWuiBuilder
from .engine import put_file
from .style import CliStyle

echo = CliStyle()


def check_node_installed():
    """Check if Node.js is installed."""
    try:
        # Run the 'node --version' command and get the output
        echo.info("Checking Node.JS ....")
        result = run_cmd(
            ['node', '--version'],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        # Extract the version number from the output, which will look like 'v20.3.1'
        version = result.stdout.strip().lstrip('v')
        # Split the version string to get the major version
        major_version = int(version.split('.')[0])
        if major_version >= 18:
            return True
        else:
            echo.error("Error: Node.js version must be >= 18")
            return False
    except subprocess.CalledProcessError:
        echo.error("Node.js is not installed. Please install Node.js first.")
        return False


def install_and_create_vite_app(project_dir, vite_args):
    """Install Vite using npm."""
    try:
        run_cmd(['npm', 'create', 'vite@latest', 'app', '-y', '--'] + vite_args, check=True)
        os.chdir(os.path.join(project_dir, "app"))
        with yaspin(text="Installing dependencies ...", color="blue") as spinner:
            spinner.color = 'blue'
            check_call([sys.executable, "-m", "pip", 'install', "pywebview", "pywui"], stdout=DEVNULL)
            check_call(["npm", 'install'], stdout=DEVNULL)
            check_call(["npm", 'install', '@pywui/app'], stdout=DEVNULL)
            spinner.color = 'green'
            spinner.ok("✔")
    except subprocess.CalledProcessError as e:
        echo.error(f"Error when creating frontend app : {e}")
        sys.exit(1)


def create_new_project(name, nv, vite_args):
    # Project dir
    project_dir = os.path.join(os.getcwd(), name)
    if not os.path.exists(project_dir):
        os.makedirs(project_dir, exist_ok=True)
    else:
        if not os.listdir(project_dir):
            echo.error("Project dir is not empty")
            return
            # main py
    put_file(os.path.join(project_dir, "main.py"), "main.py", {})
    put_file(os.path.join(project_dir, "pywui.conf.json"), "pywui.conf.json", {"name": name})
    shutil.copytree(
        os.path.join(os.path.dirname(__file__), "stubs", "icons"),
        os.path.join(project_dir, "icons"),
        dirs_exist_ok=False
    )

    if not nv:
        path = os.getcwd()
        os.chdir(project_dir)
        install_and_create_vite_app(project_dir, vite_args=vite_args)
        os.chdir(path)
    echo.success("Project has been successfully created.")


def _load_config() -> dict[str, typing.Any]:
    config_path = os.path.join(os.getcwd(), 'pywui.conf.json')
    if os.path.exists(config_path):
        with open(config_path) as f:
            try:
                return ujson.load(f)
            except ujson.JSONDecodeError:
                return {}
    return {}


def _get_icon(config):
    current_os = str.lower(platform.system().lower())
    icons: dict[str, typing.Any] = config.get("icons", {})
    return icons.get(current_os, icons.get("linux"))


@click.group()
def cli():
    pass


@cli.command()
@click.argument("name", required=True)
@click.argument("vite_args", nargs=-1, type=click.UNPROCESSED)
@click.option("-nv", "--no-vite", is_flag=True)
def new(name, vite_args, no_vite):
    """Command to create new pywui project."""
    # Check if Node.js is installed
    click.clear()
    if not check_node_installed():
        sys.exit(1)
    echo.success("Node.js is installed.")
    echo.info("Creating project ...")
    create_new_project(name, no_vite, list(vite_args))


@cli.command()
@click.argument("spec", default="main.py", required=False)
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
def pack(spec, args):
    """Command pack pywui project to single executable."""
    click.clear()
    with yaspin(text="Packing app ...", color="blue") as spinner:
        spinner.color = 'blue'
        bui = PyWuiBuilder(os.getcwd(), _load_config())
        bui.pack(spec, args)
        bui.create_installer()
        spinner.color = 'green'
        spinner.ok("✔")


@cli.command()
@click.argument("entry", default="main.py", required=False)
def run(entry):
    """Run python main.py"""
    bui = PyWuiBuilder(os.getcwd(), _load_config())
    bui.run(entry)

    # Start the vite dev server


if __name__ == '__main__':
    cli()
