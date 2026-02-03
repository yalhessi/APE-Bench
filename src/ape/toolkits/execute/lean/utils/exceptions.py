"""
LeanVerify exception handling module.
Only keep exceptions that require special handling; avoid over-engineering.
"""

# ==================== Exceptions that require special business handling ====================

class AlreadyBuildingError(Exception):
    """Workspace is already being built - need to wait for build completion"""
    pass


class AlreadyRestoringError(Exception):
    """Workspace is already being restored - need to wait for restoration completion"""
    pass


class BuildIncompleteError(Exception):
    """Build process terminated abnormally, build incomplete - need to rebuild"""
    pass


class WorkspaceFailedError(Exception):
    """Workspace is in a failed state - need to rebuild"""
    pass


class DiskSpaceError(Exception):
    """Disk space is insufficient - need to display special disk information"""
    pass
