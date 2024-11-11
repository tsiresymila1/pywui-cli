import os

from minijinja import Environment


def _loader(name: str):
    segments = []
    for segment in name.split("/"):
        if "\\" in segment or segment in (".", ".."):
            return None
        segments.append(segment)
    try:
        path = os.path.join(os.path.dirname(__file__), 'stubs', *segments)
        with open(path) as f:
            content = f.read()
            return content
    except (IOError, OSError):
        pass


env = Environment(loader=_loader)
env.add_filter('capitalize', str.capitalize)
env.add_filter('lower', str.lower)


def put_file(dst: str, template: str, context: dict = None) -> None:
    with open(dst, 'w') as f:
        content = env.render_template(template, **context)
        f.write(content)
