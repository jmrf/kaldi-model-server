import logging

import coloredlogs

from kserver import version

__version__ = version.__version__

logger = logging.getLogger(__name__)

coloredlogs.install(logger=logger, level=logging.DEBUG)
