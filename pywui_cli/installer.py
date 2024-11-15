import os
import platform
import subprocess

try:
    import msilib
except ImportError:
    msilib = None

try:
    import dmgbuild
except ImportError:
    dmgbuild = None

try:
    from debian.debfile import DebFile
except ImportError:
    DebFile = None

try:
    from rpm.spec import Spec
    from rpm.package import Package
except ImportError:
    Spec, Package = None, None


def install_dependencies():
    """Install necessary dependencies based on the operating system."""
    system = platform.system()

    if system == "Windows":
        print("Checking msilib for MSI creation...")
        if msilib is None:
            print("msilib is included with Python, please ensure it's working correctly.")
    elif system == "Darwin":
        print("Checking dmgbuild for DMG creation...")
        if dmgbuild is None:
            print("Installing dmgbuild...")
            subprocess.check_call(["pip", "install", "dmgbuild"])
    elif system == "Linux":
        if os.path.exists("/etc/debian_version"):
            print("Checking python3-debian for DEB creation...")
            if DebFile is None:
                print("Installing python3-debian...")
                subprocess.check_call(["sudo", "apt-get", "install", "-y", "python3-debian"])
        elif os.path.exists("/etc/redhat-release"):
            print("Checking rpm-py-installer for RPM creation...")
            if Spec is None or Package is None:
                print("Installing rpm-py-installer...")
                subprocess.check_call(["pip", "install", "rpm-py-installer"])

    return system


def create_msi(
        cwd,
        app_name,
        version="1.0.0",
        description="No description",
        maintainer="Your Name <youremail@example.com>",
        icon_path=None,
        output_dir="dist"
):
    """
    Creates a Windows installer (.exe) for the specified application using Inno Setup.

    :param cwd: The current directory of the application.
    :param app_name: The name of the application.
    :param version: The version of the app (default is "1.0.0").
    :param description: A short description of the app (default is "No description").
    :param maintainer: The maintainer's name and email (default is "Your Name <youremail@example.com>").
    :param icon_path: Path to an icon file for the application (optional).
    :param output_dir: Directory to save the installer (default is "dist").
    """
    # Define the paths
    from pathlib import Path
    installer_script_path = Path(cwd, f"{app_name}_installer.iss")
    binary_path = Path(cwd, 'dist', f"{app_name}.exe")
    setup_output_path = Path(output_dir)

    if not os.path.isfile(binary_path):
        raise FileNotFoundError(f"Binary file '{binary_path}' not found.")

    # Create the Inno Setup script content
    inno_script = f"""
[Setup]
AppName={app_name}
AppVersion={version}
DefaultDirName={{autopf}}\\{app_name}
DefaultGroupName={app_name}
OutputDir={setup_output_path}
OutputBaseFilename={app_name}_installer
Compression=lzma
SolidCompression=yes
LicenseFile=LICENSE.txt
AppPublisher={maintainer}
AppPublisherURL=http://www.example.com
AppSupportURL=http://www.example.com
AppUpdatesURL=http://www.example.com

[Files]
Source: "{binary_path}"; DestDir: "{{app}}"; Flags: ignoreversion

[Icons]
Name: "{{autoprograms}}\\{app_name}"; Filename: "{{app}}\\{app_name}.exe"

[Run]
Filename: "{{app}}\\{app_name}.exe"; Description: "{app_name}"; Flags: nowait postinstall skipifsilent
"""

    if icon_path:
        inno_script += f"""
[Icons]
Name: "{{autoprograms}}\\{app_name}"; Filename: "{{app}}\\{app_name}.exe"; IconFilename: "{icon_path}"
"""

    # Save the Inno Setup script
    with open(installer_script_path, 'w') as f:
        f.write(inno_script)

    # Run Inno Setup to generate the installer
    inno_setup_path = r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"  # Update the path if needed
    subprocess.run([inno_setup_path, str(installer_script_path)], check=True)

    print(f"Installer created successfully: {setup_output_path}/{app_name}_installer.exe")


def create_dmg_(cwd: any, app_name: str, icon: str, badge: str):
    """Creates a DMG installer on macOS using dmgbuild."""
    try:
        import dmgbuild
    except ImportError:
        raise ImportError("dmgbuild package is required to create DMG files on macOS.")

    binary_name = os.path.join(cwd, "dist", f"{app_name}.app")
    if not os.path.exists(binary_name):
        raise FileNotFoundError(f"{app_name} does not exist.")

    dmg_file = f"dist/{app_name}.dmg"
    dmgbuild.build_dmg(
        filename=dmg_file,
        volume_name=app_name,
        settings={
            "icon": icon,
            "files": [(f"dist/{app_name}.app", f"/Applications/{app_name}.app")],
            "badge_icon": badge
        }
    )
    print(f"DMG created: {app_name}.dmg")


def create_dmg(
        cwd,
        app_name,
        version="1.0.0",
        output_dir="dist",
        icon=None,
        custom_layout=False
):
    """
    Create a .dmg disk image for macOS from an app bundle.

    :param cwd: The working dir of the app.
    :param app_name: The name of the app.
    :param version: The version of the app (default is "1.0.0").
    :param output_dir: Directory to save the .dmg file (default is current directory).
    :param icon: Optional background image for the DMG (default is None).
    :param custom_layout: Whether to use a custom layout for the DMG (default is False).
    """
    from pathlib import Path
    import shutil
    app_bundle_path = Path(cwd) / 'dist' / f'{app_name}.app'
    dmg_output_path = Path(output_dir) / f"{app_name}-{version}.dmg"
    dmg_temp_folder = Path(cwd) / "dmg_temp"

    # Ensure the app bundle exists
    if not app_bundle_path.is_dir():
        raise FileNotFoundError(f"The app bundle {app_bundle_path} does not exist.")

    # Create a temporary folder to structure the DMG contents
    dmg_temp_folder.mkdir(parents=True, exist_ok=True)

    # Copy the app bundle to the temp folder
    app_dest = dmg_temp_folder / f"{app_name}.app"
    if not app_dest.exists():
        shutil.copytree(app_bundle_path, app_dest)

    # Create a symbolic link to Applications
    applications_link = dmg_temp_folder / "Applications"
    if not applications_link.exists():
        applications_link.symlink_to("/Applications")

    if custom_layout:
        if icon is None or not Path(icon).is_file():
            raise ValueError("For custom layout, a valid background image file must be provided.")
        # Use create-dmg for a custom layout with background
        create_dmg_command = [
            "create-dmg",
            "--volname", app_name,
            "--background", icon,
            "--window-size", "600", "400",
            "--icon-size", "100",
            "--icon", f"{app_name}.app", "175", "120",
            "--app-drop-link", "425", "120",
            str(dmg_output_path),
            str(dmg_temp_folder)
        ]
        os.system(" ".join(create_dmg_command))
    else:
        # Create DMG using hdiutil for a basic layout
        dmg_command = [
            "hdiutil", "create",
            str(dmg_output_path),
            "-volname", app_name,
            "-srcfolder", str(dmg_temp_folder),
            "-ov", "-format", "UDZO"
        ]
        os.system(" ".join(dmg_command))

    # Clean up the temporary folder
    shutil.rmtree(dmg_temp_folder, ignore_errors=True)

    print(f"Disk image created successfully: {dmg_output_path}")


# Example usage


def create_deb(
        cwd: str,
        app_name: str,
        version: str = "1.0.0",
        architecture: str = "amd64",
        description: str = "No description",
        maintainer: str = "PyWui <tsiresymila@gmail.com>",
        dependencies: str = "libc6 (>= 2.27)",
        output_dir: str = "dist",
        icon_path: str = None,
        categories: str = "Utility"
):
    """
    Creates a .deb package for the specified application.

    :param cwd: The current working directory of the application.
    :param app_name: The name of the application.
    :param version: The version of the app (default is "1.0.0").
    :param architecture: The architecture for the package (default is "amd64").
    :param description: A short description of the app (default is "No description").
    :param maintainer: The maintainer's name and email (default is "PyWui <tsiresymila@gmail.com>").
    :param dependencies: The dependencies required by the app (default is "libc6 (>= 2.27)").
    :param output_dir: Directory to save the .deb package (default is current directory).
    :param icon_path: Path to an icon file for the application (optional).
    :param categories: Categories for the .desktop file (default is "Utility").
    """

    from pathlib import Path
    import shutil
    # Define the directory structure
    root_dir = Path(cwd, 'dist', 'linux', app_name)
    debian_dir = root_dir / "DEBIAN"
    bin_dir = root_dir / "usr" / "local" / "bin"
    desktop_dir = root_dir / "usr" / "share" / "applications"
    icon_dir = root_dir / "usr" / "share" / "icons" / "hicolor" / "512x512" / "apps"

    # Create the necessary directories
    debian_dir.mkdir(parents=True, exist_ok=True)
    bin_dir.mkdir(parents=True, exist_ok=True)
    desktop_dir.mkdir(parents=True, exist_ok=True)
    if icon_path:
        icon_dir.mkdir(parents=True, exist_ok=True)

    # Copy the binary to the bin directory
    binary_path = os.path.join(cwd, 'dist', app_name)
    if not os.path.isfile(binary_path):
        raise FileNotFoundError(f"Binary file '{binary_path}' not found.")
    shutil.copy(binary_path, bin_dir / app_name)

    # Create the control file with dynamic content
    control_content = f"""Package: {app_name}
Version: {version}
Section: base
Priority: optional
Architecture: {architecture}
Depends: {dependencies}
Maintainer: {maintainer}
Description: {description}
License: MIT
"""
    control_file = debian_dir / "control"
    control_file.write_text(control_content)

    # Create the .desktop file
    desktop_content = f"""[Desktop Entry]
Name={app_name}
Comment={description}
Exec=/usr/local/bin/{app_name}
Icon=/usr/share/icons/hicolor/512x512/apps/{app_name}.png
Terminal=false
Type=Application
Categories={categories};
"""
    desktop_file = desktop_dir / f"{app_name}.desktop"
    desktop_file.write_text(desktop_content)

    # Copy the icon file if provided
    if icon_path:
        if not os.path.isfile(icon_path):
            raise FileNotFoundError(f"Icon file '{icon_path}' not found.")
        shutil.copy(icon_path, icon_dir / f"{app_name}.png")

    # Set correct permissions for the DEBIAN directory and its contents
    subprocess.run(["chmod", "-R", "755", str(debian_dir)], check=True)

    # Build the .deb package using dpkg-deb
    subprocess.run(["dpkg-deb", "--build", str(root_dir)], check=True)

    # Move the generated .deb file to the desired output directory
    output_deb_file = Path(output_dir) / f"{app_name}_{version}_{architecture}.deb"
    shutil.move(root_dir.parent / f"{app_name}.deb", output_deb_file)

    # Clean up the temporary build directory
    shutil.rmtree(root_dir.parent)
    print(f"Package created successfully: {output_deb_file}")


def create_rpm(
        cwd,
        app_name,
        version="1.0.0",
        release="1",
        architecture="x86_64",
        description="No description",
        dependencies="libc6 (>= 2.27)",
        output_dir="dist",
        icon_path=None,
        categories="Utility"
):
    """
    Creates an RPM package for the specified application.

    :param cwd: The current directory of the application.
    :param app_name: The name of the application.
    :param version: The version of the app (default is "1.0.0").
    :param release: The release version (default is "1").
    :param architecture: The architecture for the package (default is "x86_64").
    :param description: A short description of the app (default is "No description").
    :param maintainer: The maintainer's name and email.
    :param dependencies: The dependencies required by the app.
    :param output_dir: Directory to save the RPM package.
    :param icon_path: Path to an icon file for the application (optional).
    :param categories: Categories for the .desktop file (default is "Utility").
    """

    import shutil
    from pathlib import Path
    rpm_build_dir = Path(os.getenv('HOME')) / "rpmbuild"
    sources_dir = rpm_build_dir / "SOURCES"
    specs_dir = rpm_build_dir / "SPECS"
    rpm_dir = rpm_build_dir / "RPMS" / architecture
    desktop_file_name = f"{app_name}.desktop"
    binary_path = Path(cwd, 'dist', app_name)

    # Ensure RPM build directories exist
    for dir_path in [sources_dir, specs_dir, rpm_dir]:
        dir_path.mkdir(parents=True, exist_ok=True)

    # Copy the binary to SOURCES
    if not os.path.isfile(binary_path):
        raise FileNotFoundError(f"Binary file '{binary_path}' not found.")
    shutil.copy(binary_path, sources_dir / app_name)

    # Create the .desktop file for system's application menu
    desktop_content = f"""[Desktop Entry]
Name={app_name}
Comment={description}
Exec=/usr/local/bin/{app_name}
Icon=/usr/share/icons/hicolor/512x512/apps/{app_name}.png
Terminal=false
Type=Application
Categories={categories};
"""
    desktop_file = sources_dir / desktop_file_name
    desktop_file.write_text(desktop_content)

    # Copy the icon file if provided
    if icon_path:
        if not os.path.isfile(icon_path):
            raise FileNotFoundError(f"Icon file '{icon_path}' not found.")
        icon_target_dir = sources_dir / "icons" / "hicolor" / "512x512" / "apps"
        icon_target_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(icon_path, icon_target_dir / f"{app_name}.png")

    # Create the spec file
    spec_content = f"""
Name:           {app_name}
Version:        {version}
Release:        {release}
Summary:        {description}
License:        GPL
Group:          Applications/System
Architecture:   {architecture}
Requires:       {dependencies}

%description
{description}

%files
%attr(0755,root,root) /usr/local/bin/{app_name}
%attr(0644,root,root) /usr/share/applications/{desktop_file_name}
%attr(0644,root,root) /usr/share/icons/hicolor/512x512/apps/{app_name}.png

%post
update-desktop-database &> /dev/null || :

%postun
update-desktop-database &> /dev/null || :
"""

    spec_file = specs_dir / f"{app_name}.spec"
    spec_file.write_text(spec_content)

    # Build the RPM package
    subprocess.run(["rpmbuild", "-ba", str(spec_file)], check=True)
    # Move the generated RPM package to the output directory
    rpm_package_file = rpm_dir / f"{app_name}-{version}-{release}.{architecture}.rpm"
    shutil.move(rpm_package_file, Path(output_dir) / rpm_package_file.name)

    print(f"Package created successfully: {output_dir}/{rpm_package_file.name}")
