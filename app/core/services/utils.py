from logging import Logger, getLogger


class ServiceUtils:
    def __init__(self, logger: Logger | None = None):
        self.logger = logger or getLogger(__name__)
