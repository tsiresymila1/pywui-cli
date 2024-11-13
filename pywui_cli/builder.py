import os
import platform
import subprocess
import sys
import time
import typing
from subprocess import Popen
from typing import Union

from .style import CliStyle

echo = CliStyle()


class PyWuiBuilder:
    vite_process: Union[Popen, None] = None
    webview_process: Union[Popen, None] = None

    def __init__(self, cwd: str, config: dict[str, any]):
        self.cwd = cwd
        self.config = config

    def _stream_output(self, entry: str):
        """Handle output from both vite and python processes."""
        while True:
            if self.vite_process.poll() is not None:
                echo.info("Vite process has finished.")
                break

            if self.webview_process and self.webview_process.poll() is not None:
                echo.info("App process has finished.")
                break
            vite_output = self.vite_process.stdout.readline()
            if vite_output:
                if ("Local:" in vite_output or "Network: " in vite_output) and self.webview_process is None:
                    time.sleep(1)
                    self.webview_process = Popen(
                        [f"{sys.executable} {entry}"],
                        universal_newlines=True,
                        shell=True
                    )
                echo.info(f"[Vite] {vite_output.strip()}")

    def run(self, entry: str):
        vite_folder = os.path.join(self.cwd, "app")
        self.vite_process = Popen(
            ["npm run dev"],
            cwd=vite_folder,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            universal_newlines=True
        )
        # Start the python script
        try:
            # Monitor the python script
            self._stream_output(entry)
        except KeyboardInterrupt:
            echo.error("Interrupted by user. Exiting.")
        finally:
            # Ensure both processes are terminated on exit
            echo.success("Terminating ..")
            if self.vite_process:
                self.vite_process.terminate()
            if self.webview_process:
                self.webview_process.terminate()
            echo.success("Terminated")

    def _get_icon(self):
        current_os = str.lower(platform.system().lower())
        icons: dict[str, typing.Any] = self.config.get("icons", {})
        return icons.get(current_os, icons.get("linux"))

    def create_installer(self):
        name: str = self.config.get("name", "pywuiapp")
        from .installer import install_dependencies, create_deb, create_dmg, create_msi, create_rpm
        system = install_dependencies()
        if system == "Windows":
            print(f"Creating MSI for {name} on Windows...")
            create_msi(self.cwd, name)
        elif system == "Darwin":
            print(f"Creating DMG for {name} on macOS...")
            create_dmg(
                self.cwd,
                name,
                icon=self._get_icon(),
                badge=self._get_icon()
            )
        elif system == "Linux":
            if os.path.exists("/etc/debian_version"):
                print(f"Creating DEB for {name} on Debian-based Linux...")
                create_deb(self.cwd, name)
            elif os.path.exists("/etc/redhat-release"):
                print(f"Creating RPM for {name} on Red Hat-based Linux...")
                create_rpm(self.cwd, name)
            else:
                print("Unsupported Linux distribution. Only Debian-based and Red Hat-based systems are supported.")
        else:
            print(f"Unsupported operating system: {system}")

    def pack(self, spec: str, args: tuple):
        try:
            import pyinstaller
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", 'install', "pyinstaller"], stdout=subprocess.DEVNULL)
        os.chdir(os.path.join(self.cwd, "app"))
        build_command = ["npm", "run", "build"]
        subprocess.check_call(build_command, stdout=subprocess.DEVNULL)
        os.chdir(self.cwd)
        icon = self._get_icon()
        name = self.config.get("name", "pywui")
        dist = self.config.get("static", {}).get("dist", "app/dist")
        freeze_command = [
                             'pyinstaller',
                             '-n', f'{name}',
                             '--onefile',
                             '--noconfirm',
                             '--add-data', f'{dist}:.',
                             '--add-data', 'pywui.conf.json:.',
                             '--add-data', 'icons:icons',
                             f'--icon={icon}',
                             '--windowed',
                         ] + list(args) + [spec]
        subprocess.check_call(freeze_command, stdout=subprocess.DEVNULL)
