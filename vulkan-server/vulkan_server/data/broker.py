import hashlib
import json
from datetime import datetime, timezone

import requests
from requests.adapters import HTTPAdapter
from sqlalchemy.orm import Session
from urllib3.util import Retry

from vulkan_server import schemas
from vulkan_server.db import DataObject, RunDataCache
from vulkan_server.logger import init_logger

logger = init_logger("data_broker")


class DataBroker:
    def __init__(self, db: Session, spec: schemas.DataSource) -> None:
        self.db = db
        self.spec = spec

    def get_data(self, request_body: dict) -> DataObject:
        cache = CacheManager(self.db, self.spec)
        key = make_cache_key(self.spec, request_body)

        if self.spec.caching.enabled:
            logger.debug("Trying to get data from cache")
            data = cache.get_data(key)

            if data is not None:
                return data

        logger.debug(
            f"Request: body {request_body}\n headers {self.spec.request.headers} \n"
            f"url {self.spec.request.url}"
        )
        req = make_request(self.spec, request_body)
        response = requests.Session().send(req, timeout=self.spec.request.timeout)
        response.raise_for_status()

        if response.status_code == 200:
            data = DataObject(
                key=key,
                value=response.content,
                project_id=self.spec.project_id,
                data_source_id=self.spec.data_source_id,
            )
            self.db.add(data)
            self.db.commit()
            logger.info(f"Stored object with id {data.data_object_id}")

            if self.spec.caching.enabled:
                cache.set_cache(key, data.data_object_id)

            return data


class CacheManager:
    def __init__(self, db: Session, spec: schemas.DataSource) -> None:
        self.db = db
        self.spec = spec

    def get_data(self, key: str) -> DataObject | None:
        cache = self.db.query(RunDataCache).filter_by(key=key).first()

        if cache is None:
            return None

        data = (
            self.db.query(DataObject)
            .filter_by(data_object_id=cache.data_object_id)
            .first()
        )

        ttl = self.spec.caching.ttl
        elapsed = (datetime.now(timezone.utc) - data.created_at).total_seconds()

        if ttl is not None and elapsed > ttl:
            logger.info(f"Deleting cache with key {key}: TTL expired")
            self.db.delete(cache)
            self.db.commit()
            return None

        return data

    def set_cache(self, key: str, data_object_id: str) -> None:
        logger.info(f"Setting cache with key {key}")
        cache = RunDataCache(
            key=key,
            data_object_id=data_object_id,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(cache)
        self.db.commit()


def make_cache_key(spec: schemas.DataSource, body: dict) -> str:
    # TODO: make sure all fields in body are json serializable
    content = dict(data_source_id=str(spec.data_source_id), body=body)
    content_str = json.dumps(content, sort_keys=True)
    return hashlib.md5(content_str.encode("utf-8")).hexdigest()


def make_request(spec: schemas.DataSource, body: dict) -> requests.Request:
    if spec.request.headers.get("Content-Type") == "application/json":
        json = body
        data = None
    else:
        json = None
        data = body

    retry = Retry(
        total=spec.retry.max_retries,
        backoff_factor=spec.retry.backoff_factor,
        status_forcelist=spec.retry.status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    req = requests.Request(
        method=spec.request.method,
        url=spec.request.url,
        headers=spec.request.headers,
        params=spec.request.params,
        data=data,
        json=json,
    ).prepare()
    return req


def configure_headers(spec: schemas.DataSource) -> dict:
    headers = spec.request.headers
    if headers is None:
        headers = {}

    # for key, value in headers.items():
    #     if isinstance(value, ConfigurableParameter):
    #         headers[key] = value.get_value()
    #     if isinstance(value, SecretKey):
    #         headers[key] = value.get_secret()

    return headers


def configure_params(spec: schemas.DataSource) -> dict:
    params = spec.request.params
    if params is None:
        params = {}

    # for key, value in params.items():
    #     if isinstance(value, ConfigurableParameter):
    #         params[key] = value.get_value()
    #     if isinstance(value, SecretKey):
    #         params[key] = value.get_secret()

    return params
