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
        cwd: any,
        app_name: str,
        description: str = None,
        arch: str = "amd64",
        version: str = "1.0",
        maintainer: str = None,
        maintainer_email: str = None
):
    """Creates a DEB installer on Debian-based Linux using python-debian."""
    try:
        from debian.debfile import DebFile
    except ImportError:
        raise ImportError("python-debian package is required to create DEB files on Debian-based Linux.")

    binary_name = os.path.join(cwd, f"dist/{app_name}")
    if not os.path.exists(binary_name):
        raise FileNotFoundError(f"{binary_name} does not exist.")

    deb = DebFile(f"dist/{app_name}.deb")
    deb.data.add_file(binary_name, f"/usr/local/bin/{app_name.lower()}")
    deb.control["Package"] = app_name.lower()
    deb.control["Version"] = version
    deb.control["Architecture"] = arch
    deb.control["Maintainer"] = f"{maintainer or 'Pywui'} <{maintainer_email or 'tsiresymila@gmail.com'}>"
    deb.control["Description"] = description or f"A pywui app called {app_name}"
    deb.write(f"{app_name}.deb")
    print(f"DEB created: {app_name}.deb")


def create_rpm(
        cwd: any,
        app_name: str,
        description: str = None,
        version: str = "1.0",
        release: str = "1",
        license: str = "MIT"
):
    """Creates an RPM installer on Red Hat-based Linux using rpm-py-installer."""
    try:
        from rpm.spec import Spec
        from rpm.package import Package
    except ImportError:
        if Spec is None or Package is None:
            raise ImportError("rpm-py-installer package is required to create RPM files on Red Hat-based Linux.")

    binary_name = os.path.join(cwd, f"dist/{app_name}")
    if not os.path.exists(binary_name):
        raise FileNotFoundError(f"{binary_name} does not exist.")

    spec = Spec()
    spec.name = app_name.lower()
    spec.version = version
    spec.release = release
    spec.summary = description or f"Description of {app_name}"
    spec.license = license
    package = Package(spec)
    package.add_file(binary_name, f"/usr/local/bin/{app_name.lower()}")
    package.write(f"dist/{app_name}.rpm")
    print(f"RPM created: {app_name}.rpm")
