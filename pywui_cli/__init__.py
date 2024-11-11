import os.path
import shutil
import subprocess
import sys
import platform
import typing

import rich_click as click
import ujson
from yaspin import yaspin
from subprocess import DEVNULL, check_call, run

from .style import CliStyle
from .engine import put_file

echo = CliStyle()


def check_node_installed():
    """Check if Node.js is installed."""
    try:
        # Run the 'node --version' command and get the output
        echo.info("Checking Node.JS ....")
        result = run(
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
        run(['npm', 'create', 'vite@latest', 'app', '-y', '--'] + list(vite_args), check=True)
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


def create_new_project(name, vite_args):
    # Project dir
    project_dir = os.path.join(os.getcwd(), name)
    if os.path.exists(project_dir):
        echo.error("Project already exists. Please remove or rename it first.")
        return
    os.makedirs(project_dir, exist_ok=True)
    # main py
    put_file(os.path.join(project_dir, "main.py"), "main.py", {})
    put_file(os.path.join(project_dir, "pywui.conf.json"), "pywui.conf.json", {"name": name})
    shutil.copytree(
        os.path.join(os.path.dirname(__file__), "stubs", "icons"),
        os.path.join(project_dir, "icons"),
        dirs_exist_ok=False
    )
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
def new(name, vite_args):
    """Command to create new pywui project."""
    # Check if Node.js is installed
    click.clear()
    if not check_node_installed():
        sys.exit(1)
    echo.success("Node.js is installed.")
    echo.info("Creating project ...")
    create_new_project(name, vite_args)


@cli.command()
@click.argument("spec", nargs=-1, type=click.UNPROCESSED)
def pack(spec):
    """Command pack pywui project to single executable."""
    click.clear()
    with yaspin(text="Packing app  ...", color="blue") as spinner:
        spinner.color = 'blue'
        try:
            import pyinstaller
        except ImportError:
            check_call([sys.executable, "-m", "pip", 'install', "pyinstaller"], stdout=DEVNULL)
        current = os.getcwd()
        os.chdir(os.path.join(current, "app"))
        build_command = ["npm", "run", "build"]
        check_call(build_command, stdout=DEVNULL)
        os.chdir(current)
        config = _load_config()
        icon = _get_icon(config)
        name = config.get("name", "pywui")
        freeze_command = [
                             'pyinstaller',
                             '-n', f'{name}',
                             '--onefile',
                             '--noconfirm',
                             '--add-data', 'app/dist:.',
                             '--add-data', 'pywui.conf.json:.',
                             '--add-data', 'icons:icons',
                             f'--icon={icon}',
                             '--windowed',
                             'main.py'
                         ] + list(spec)
        check_call(freeze_command, stdout=DEVNULL)
        spinner.color = 'green'
        spinner.ok("✔")


if __name__ == '__main__':
    cli()
