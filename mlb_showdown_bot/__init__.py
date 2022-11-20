try:
    # ASSUME THIS IS A SUBMODULE IN A PACKAGE
    from .version import __version__
except ImportError:
    # USE LOCAL IMPORT 
    from version import __version__

__version__ = __version__