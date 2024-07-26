import os
from collections.abc import Sequence
from pickle import dump, load

import requests
from dagster import ConfigurableIOManager, InputContext, IOManager, OutputContext

from .run import RUN_CONFIG_KEY, VulkanRunConfig
from .step_metadata import StepMetadata


class MyIOManager(ConfigurableIOManager):
    root_path: str

    def _get_path(self, identifier: Sequence[str]) -> str:
        return os.path.join(self.root_path, *identifier)

    def handle_output(self, context: OutputContext, obj):
        path = self._get_path(context.get_identifier())
        dirname = os.path.dirname(path)
        os.makedirs(dirname, exist_ok=True)
        with open(path, "wb") as f:
            dump(obj, f)

    def load_input(self, context: InputContext):
        path = self._get_path(context.get_identifier())
        with open(path, "rb") as f:
            return load(f)


class PublishMetadataIOManager(IOManager):
    def __init__(self, url: str):
        self._url = url

    def handle_output(self, context: OutputContext, obj):
        if context.name != "metadata":
            raise NotImplementedError("Currently only supports metadata")

        if not isinstance(obj, StepMetadata):
            raise TypeError(f"Expected StepMetadata, got {type(obj)}")

        try:
            response = requests.post(
                self._url,
                data={
                    "step_name": context.step_key,
                    "node_type": obj.node_type,
                    "start_time": obj.start_time,
                    "end_time": obj.end_time,
                    "error": obj.error,
                },
            )
            if response.status_code != 200:
                msg = f"ERROR {response.status_code}: Failed to publish metadata: {response.text}"
                raise ValueError(msg)
        except Exception as e:
            msg = f"Failed to publish metadata for step {context.get_identifier()}"
            raise ValueError(msg) from e

    def load_input(self, context: InputContext):
        raise NotImplementedError("Currently only supports metadata output")


def metadata_io_manager(context) -> PublishMetadataIOManager:
    run_config: VulkanRunConfig = getattr(context.resources, RUN_CONFIG_KEY)
    policy_id = run_config.policy_id
    run_id = run_config.run_id
    server_url = run_config.server_url
    url = f"{server_url}/policies/{policy_id}/runs/{run_id}/metadata"

    return PublishMetadataIOManager(url=url)
