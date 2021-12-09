import logging

import coloredlogs

logger = logging.getLogger(__name__)

coloredlogs.install(logger=logger, level=logging.DEBUG)
