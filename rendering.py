import os

from jinja2 import Environment, FileSystemLoader


def render_to_file(template_name, filename, **kwargs):
    env = Environment(loader=FileSystemLoader(os.path.dirname(__file__) + '/templates'))
    template = env.get_template(template_name)

    with open(filename, 'w') as f:
        f.write(template.render(**kwargs))
