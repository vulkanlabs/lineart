from requests import Session

from vulkan.cli.auth import retrieve_credentials


def init_session() -> Session:
    session = Session()
    session.headers.update(retrieve_credentials())
    return session
