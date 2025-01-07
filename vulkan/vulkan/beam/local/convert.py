from vulkan_public.schemas import DataSourceSpec

from vulkan.beam.pipeline import BeamPipelineBuilder


def build_beam_policy(
    policy,
    data_sources: list[DataSourceSpec],
    output_path: str,
    config_variables: dict[str, str] | None = None,
):
    if config_variables is None:
        config_variables = {}

    data_sources_map = {}
    for source in data_sources:
        assert isinstance(
            source, DataSourceSpec
        ), f"Data sources should be an instance of DataSourceSpec, got {source}"
        if source.name in data_sources_map:
            raise ValueError(f"Duplicate data source name: {source.name}")
        data_sources_map[source.name] = source

    builder = BeamPipelineBuilder(
        policy=policy,
        output_path=output_path,
        data_sources=data_sources_map,
        config_variables=config_variables,
    )
    return builder
