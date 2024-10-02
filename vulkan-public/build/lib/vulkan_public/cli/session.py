from requests import Session


def init_session(headers: dict) -> Session:
    session = Session()
    session.headers.update(headers)
    return session
