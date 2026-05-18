class LightRAGDeployError(Exception):
    """Base class for deployment-control errors."""


class DeploymentDisabledError(LightRAGDeployError):
    pass


class DomainNotFoundError(LightRAGDeployError):
    pass


class DomainAlreadyExistsError(LightRAGDeployError):
    pass


class PortConflictError(LightRAGDeployError):
    pass


class PermanentDeleteDisabledError(LightRAGDeployError):
    pass
