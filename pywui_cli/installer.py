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
        cwd: any,
        app_name: str,
        manufacturer: str = "PyWui",
        title: str = None,
        description: str = None
):
    """Creates an MSI installer on Windows using msilib."""
    try:
        import msilib
    except ImportError:
        raise ImportError("msilib package is required to create MSI files on Windows.")

    exe_name = os.path.join(cwd, f"dist/{app_name}.exe")
    if not os.path.exists(exe_name):
        raise FileNotFoundError(f"{exe_name} does not exist.")

    db = msilib.init_database(f"dist/{app_name}.msi", msilib.schema, app_name, "1.0.0")
    msilib.add_tables(db, msilib.schema)
    msilib.add_data(db, 'Property', [('ProductName', app_name), ('Manufacturer', manufacturer or 'PyWui')])

    msilib.add_data(db, 'Directory', [
        ('TARGETDIR', 'SourceDir', None, None),
        ('ProgramFilesFolder', 'TARGETDIR', 'ProgramFilesFolder', None),
        (f"{app_name}Dir", 'ProgramFilesFolder', app_name, None)
    ])

    feature = msilib.Feature(
        db, "DefaultFeature",
        title or "Default Feature",
        description or "Everything",
        1,
        directory=f"{app_name}Dir"
    )
    cab = msilib.CAB(f"{app_name}Files")
    cab.add(exe_name, f"{app_name}.exe")
    cab.commit(db)

    msilib.add_data(db, 'File', [
        (f"{app_name}.exe", f"{app_name}Dir", f"{app_name}.exe", None, 0, 0, f"{app_name}Files", None, None)
    ])

    msilib.add_data(db, 'Component', [
        ('AppExecutable', f"{app_name}Dir", f"{app_name}.exe", None, None, None, None, None, None, None, 0)
    ])

    msilib.add_data(db, 'FeatureComponents', [
        ('DefaultFeature', 'AppExecutable')
    ])
    db.Commit()
    print(f"MSI created: {app_name}.msi")


def create_dmg(cwd: any, app_name: str, icon: str, badge: str):
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
