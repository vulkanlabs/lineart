import os
from collections.abc import Sequence
from pickle import dump, load

from dagster import ConfigurableIOManager, InputContext, OutputContext


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
