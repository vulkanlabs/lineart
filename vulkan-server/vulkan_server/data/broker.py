import hashlib
import json
from datetime import datetime, timezone
from logging import Logger

import requests
from sqlalchemy.orm import Session

from vulkan.connections import make_request
from vulkan_server import schemas
from vulkan_server.db import DataObject, RunDataCache


class DataBroker:
    def __init__(self, db: Session, logger: Logger, spec: schemas.DataSource) -> None:
        self.db = db
        self.logger = logger
        self.spec = spec

    def get_data(
        self, node_variables: dict, env_variables: dict
    ) -> schemas.DataBrokerResponse:
        cache = CacheManager(self.db, self.logger, self.spec)
        key = make_cache_key(self.spec, node_variables)

        if self.spec.caching.enabled:
            data = cache.get_data(key)

            if data is not None:
                return schemas.DataBrokerResponse(
                    data_object_id=data.data_object_id,
                    origin=schemas.DataObjectOrigin.CACHE,
                    key=key,
                    value=data.value,
                )

        # self.logger.info(f"Fetching data for key {key} from source {self.spec.source.url}")
        req = make_request(self.spec.source, node_variables, env_variables)
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
            # self.logger.info(f"Stored object with id {data.data_object_id}")

            if self.spec.caching.enabled:
                cache.set_cache(key, data.data_object_id)

            return schemas.DataBrokerResponse(
                data_object_id=data.data_object_id,
                origin=schemas.DataObjectOrigin.REQUEST,
                key=key,
                value=data.value,
            )


class CacheManager:
    def __init__(self, db: Session, logger: Logger, spec: schemas.DataSource) -> None:
        self.db = db
        self.logger = logger
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
            # self.logger.info(f"Deleting cache with key {key}: TTL expired")
            self.db.delete(cache)
            self.db.commit()
            return None

        return data

    def set_cache(self, key: str, data_object_id: str) -> None:
        # self.logger.info(f"Setting cache with key {key}")
        cache = RunDataCache(
            key=key,
            data_object_id=data_object_id,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(cache)
        self.db.commit()


def make_cache_key(spec: schemas.DataSource, variables: dict) -> str:
    # TODO: make sure all fields in body are json serializable
    content = dict(data_source_id=str(spec.data_source_id), variables=variables)
    content_str = json.dumps(content, sort_keys=True)
    return hashlib.md5(content_str.encode("utf-8")).hexdigest()
