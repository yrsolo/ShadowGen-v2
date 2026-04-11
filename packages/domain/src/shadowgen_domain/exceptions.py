class ShadowGenDomainError(Exception):
    """Base domain error."""


class JobNotFoundError(ShadowGenDomainError):
    pass


class AssetNotFoundError(ShadowGenDomainError):
    pass


class JobStateError(ShadowGenDomainError):
    pass
