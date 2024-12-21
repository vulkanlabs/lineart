from typing import Any

from vulkan.beam.pipeline import BeamPipelineBuilder, DataEntryConfig


def build_beam_policy(
    policy,
    data_sources: dict[str, Any],
    output_path: str,
    config_variables: dict[str, str] | None = None,
):
    data_sources_map = {
        name: DataEntryConfig(source=source) for name, source in data_sources.items()
    }

    builder = BeamPipelineBuilder(
        policy=policy,
        output_path=output_path,
        data_sources=data_sources_map,
        config_variables=config_variables,
    )
    return builder
