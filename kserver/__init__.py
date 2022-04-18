import logging

import coloredlogs

from kserver import version

__version__ = version.__version__

logger = logging.getLogger(__name__)

# TODO: Configure level by CLI
coloredlogs.install(logger=logger, level=logging.DEBUG)
