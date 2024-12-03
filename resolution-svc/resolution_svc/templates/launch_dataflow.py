import json
import logging
from argparse import ArgumentParser
from typing import Any

from apache_beam.options.pipeline_options import PipelineOptions
from vulkan.beam.pipeline import BeamPipelineBuilder, DataEntryConfig
from vulkan.environment.loaders import resolve_policy

logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.INFO)

def launch_pipeline(
    backfill_id: str,
    data_sources: dict[str, Any],
    module_name: str,
    components_path: str,
    output_path: str,
    config_variables: dict[str, str] | None = None,
    other_args: list[str] = [],
):
    policy = resolve_policy(module_name, components_path)

    data_sources_map = {
        name: DataEntryConfig(source=source) for name, source in data_sources.items()
    }

    pipeline_args = [
        "--save_main_session",
        "--sdk_location", "container",
    ] + other_args

    pipeline_options = PipelineOptions(pipeline_args)
    pipeline = BeamPipelineBuilder(
        policy=policy,
        backfill_id=backfill_id,
        output_path=output_path,
        data_sources=data_sources_map,
        config_variables=config_variables,
        pipeline_options=pipeline_options,
    ).build()

    pipeline.run()


if __name__ == "__main__":
    parser = ArgumentParser()
    # Run config args
    parser.add_argument("--backfill_id", type=str)
    parser.add_argument("--output_path", type=str)
    parser.add_argument("--data_sources", type=str)
    parser.add_argument("--config_variables", type=str)
    # Code location args
    parser.add_argument("--module_name", type=str)
    parser.add_argument("--components_path", type=str)
    args, unknown_args = parser.parse_known_args()

    data_sources = json.loads(args.data_sources)

    if args.config_variables:
        config_variables = json.loads(args.config_variables)
    else:
        config_variables = None

    launch_pipeline(
        backfill_id=args.backfill_id,
        data_sources=data_sources,
        module_name=args.module_name,
        components_path=args.components_path,
        output_path=args.output_path,
        config_variables=config_variables,
        other_args=unknown_args,
    )
