"""Test file for Chain Constructors pattern detection."""


class SimpleClass:
    """
    Simple class - should not be flagged.

    ::: This is-in-layer Test-Layer.
    ::: This is a fixture.
    """

    def __init__(self, name):
        self.name = name


class MediumComplexity:
    """Medium complexity - 6 parameters."""

    def __init__(self, host, port, username, password, database, timeout=30):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.database = database
        self.timeout = timeout


class HighComplexity:
    """High complexity - 10 parameters, good candidate for Chain Constructors."""

    def __init__(self, host, port, username, password, database,
                 timeout=30, retry_count=3, ssl_enabled=False,
                 pool_size=10, debug=False):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.database = database
        self.timeout = timeout
        self.retry_count = retry_count
        self.ssl_enabled = ssl_enabled
        self.pool_size = pool_size
        self.debug = debug


class TelescopingConstructor:
    """Telescoping constructor - many defaults, perfect for factory methods."""

    def __init__(self, name, age=None, email=None, phone=None,
                 address=None, city=None, country=None):
        self.name = name
        self.age = age
        self.email = email
        self.phone = phone
        self.address = address
        self.city = city
        self.country = country


class WithFactoryMethods:
    """Already has factory methods - should be noted."""

    def __init__(self, config, logger, cache, database, metrics):
        self.config = config
        self.logger = logger
        self.cache = cache
        self.database = database
        self.metrics = metrics

    @classmethod
    def from_config(cls, config_path):
        """Factory method from config file."""
        # Would load config and create dependencies
        pass

    @classmethod
    def from_environment(cls):
        """Factory method from environment variables."""
        # Would read environment and create instance
        pass
