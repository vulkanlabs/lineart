import hashlib
import json
from datetime import datetime, timezone

import requests
from sqlalchemy.orm import Session

from vulkan.connections import make_request
from vulkan_server import schemas
from vulkan_server.db import DataObject, RunDataCache
from vulkan_server.logger import init_logger

logger = init_logger("data_broker")


class DataBroker:
    def __init__(self, db: Session, spec: schemas.DataSource) -> None:
        self.db = db
        self.spec = spec

    def get_data(
        self, request_body: dict, variables: dict
    ) -> schemas.DataBrokerResponse:
        cache = CacheManager(self.db, self.spec)
        key = make_cache_key(self.spec, request_body, variables)

        if self.spec.caching.enabled:
            logger.debug("Trying to get data from cache")
            data = cache.get_data(key)

            if data is not None:
                return schemas.DataBrokerResponse(
                    data_object_id=data.data_object_id,
                    origin=schemas.DataObjectOrigin.CACHE,
                    key=key,
                    value=data.value,
                )

        logger.debug(
            f"Request: body {request_body}\n headers {self.spec.source.headers} \n"
            f"url {self.spec.source.url}"
        )
        # TODO: validate request_body is compatible with spec.source.body_schema
        req = make_request(self.spec.source, request_body, variables)
        response = requests.Session().send(req, timeout=self.spec.source.timeout)
        response.raise_for_status()

        if response.status_code == 200:
            data = DataObject(
                key=key,
                value=response.content,
                data_source_id=self.spec.data_source_id,
            )
            self.db.add(data)
            self.db.commit()
            logger.info(f"Stored object with id {data.data_object_id}")

            if self.spec.caching.enabled:
                cache.set_cache(key, data.data_object_id)

            return schemas.DataBrokerResponse(
                data_object_id=data.data_object_id,
                origin=schemas.DataObjectOrigin.REQUEST,
                key=key,
                value=data.value,
            )


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


def make_cache_key(spec: schemas.DataSource, body: dict, variables: dict) -> str:
    # TODO: make sure all fields in body are json serializable
    content = dict(
        data_source_id=str(spec.data_source_id), body=body, variables=variables
    )
    content_str = json.dumps(content, sort_keys=True)
    return hashlib.md5(content_str.encode("utf-8")).hexdigest()
