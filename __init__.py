bl_info = {
    "name": "UV Kit",
    "author": "Benjamin Sauder",
    "version": (1, 0),
    "blender": (4, 0, 0),
    "location": "UV/Image editor > Tool Panel, UV/Image editor UVs > menu",
    "description": "Some quality of life improvements to uv editing",
    "warning": "",
    "wiki_url": "",
    "category": "UV",
}


import importlib

modules = (
    ".operators",
    ".ui",
    ".uv_layers",
)


def import_modules():
    for module in modules:
        print(f"{module} - {__package__}")
        importlib.import_module(module, __package__)


def reimport_modules():
    for module in modules:
        want_reload_module = importlib.import_module(module, __package__)
        importlib.reload(want_reload_module)


import_modules()
reimport_modules()

from . import operators
from . import ui
from . import uv_layers

register_modules = [
    operators,
    ui,
    uv_layers,
]


def register():
    for module in register_modules:
        module.register()


def unregister():
    for module in register_modules:
        module.unregister()


if __name__ == "__main__":
    register()
