class UpstreamWeatherError(Exception):
    """Open-Meteo could not return usable data."""


class StorageUnavailableError(Exception):
    """The configured object store could not complete the request."""


class StoredFileNotFoundError(Exception):
    """The requested stored object does not exist."""


class StoredFileInvalidError(Exception):
    """The stored object is not valid weather JSON."""
