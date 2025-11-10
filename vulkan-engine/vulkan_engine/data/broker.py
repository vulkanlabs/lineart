import csv
import hashlib
import io
import json
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from logging import Logger

from sqlalchemy.orm import Session
from vulkan.connections import HTTPConfig, ResponseType
from vulkan.http_client import HTTPClient

from vulkan_engine import schemas
from vulkan_engine.db import DataObject, RunDataCache


class DataBroker:
    def __init__(self, db: Session, logger: Logger, spec: schemas.DataSource) -> None:
        self.db = db
        self.logger = logger
        self.spec = spec

    def get_data(
        self,
        configured_params: dict,
        env_variables: dict,
        auth_headers: dict | None = None,
        auth_params: dict | None = None,
    ) -> schemas.DataBrokerResponse:
        cache = CacheManager(self.db, self.logger, self.spec)
        key = make_cache_key(self.spec, configured_params)

        if self.spec.caching.enabled:
            data = cache.get_data(key)

            if data is not None:
                return schemas.DataBrokerResponse(
                    data_object_id=data.data_object_id,
                    origin=schemas.DataObjectOrigin.CACHE,
                    key=key,
                    value=self._format_data(data.value),
                    start_time=None,
                    end_time=None,
                    error=None,
                )

        start_time = time.time()

        # Create request with authentication
        config = HTTPConfig(
            url=self.spec.source.url,
            method=self.spec.source.method,
            headers=self.spec.source.headers or {},
            params=self.spec.source.params or {},
            body=self.spec.source.body or {},
            timeout=self.spec.source.timeout,
            retry=self.spec.source.retry,
            response_type=self.spec.source.response_type,
        )
        client = HTTPClient(config)
        response = client.execute_raw(
            configured_params,
            env_variables,
            extra_headers=auth_headers,
            extra_params=auth_params,
        )

        response.raise_for_status()
        end_time = time.time()

        if response.status_code == 200:
            data = DataObject(
                key=key,
                value=response.content,
                data_source_id=self.spec.data_source_id,
            )
            self.db.add(data)
            self.db.commit()

            if self.spec.caching.enabled:
                cache.set_cache(key, data.data_object_id)

            return schemas.DataBrokerResponse(
                data_object_id=data.data_object_id,
                origin=schemas.DataObjectOrigin.REQUEST,
                key=key,
                value=self._format_data(data.value),
                start_time=start_time,
                end_time=end_time,
                error=None,
            )

    def _format_data(self, value: bytes):
        data = value.decode("utf-8")
        if (
            not hasattr(self.spec.source, "response_type")
            or self.spec.source.response_type is None
            or self.spec.source.response_type == ResponseType.PLAIN_TEXT.value
        ):
            return data

        response_type = self.spec.source.response_type

        if response_type == ResponseType.JSON.value:
            return json.loads(data)
        elif response_type == ResponseType.XML.value:
            return _xml_to_dict(ET.fromstring(data))
        elif response_type == ResponseType.CSV.value:
            csv_reader = csv.DictReader(io.StringIO(data))
            return list(csv_reader)
        return data


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


def _xml_to_dict(element: ET.Element) -> dict:
    """Convert XML element to dictionary"""
    result = {}

    # Add attributes
    if element.attrib:
        result.update(element.attrib)

    # Add text content
    if element.text and element.text.strip():
        if len(element) == 0:  # No children
            return element.text.strip()
        else:
            result["text"] = element.text.strip()

    # Add children
    for child in element:
        child_data = _xml_to_dict(child)
        if child.tag in result:
            # Convert to list if multiple elements with same tag
            if not isinstance(result[child.tag], list):
                result[child.tag] = [result[child.tag]]
            result[child.tag].append(child_data)
        else:
            result[child.tag] = child_data

    return result
