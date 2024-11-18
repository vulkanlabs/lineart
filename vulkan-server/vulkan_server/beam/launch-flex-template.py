import os

from fastapi import Depends
from google.cloud import dataflow_v1beta3 as dataflow
from pydantic.dataclasses import dataclass


@dataclass
class DataflowConfig:
    service_account: str
    machine_type: str
    temp_location: str
    staging_location: str
    region: str = "us-central1"


def get_dataflow_config() -> DataflowConfig:
    GCP_DATAFLOW_SERVICE_ACCOUNT_EMAIL = os.getenv("GCP_DATAFLOW_SERVICE_ACCOUNT_EMAIL")
    GCP_DATAFLOW_MACHINE_TYPE = os.getenv("GCP_DATAFLOW_MACHINE_TYPE")
    GCP_DATAFLOW_TEMP_LOCATION = os.getenv("GCP_DATAFLOW_TEMP_LOCATION")
    GCP_DATAFLOW_STAGING_LOCATION = os.getenv("GCP_DATAFLOW_STAGING_LOCATION")
    GCP_DATAFLOW_REGION = os.getenv("GCP_DATAFLOW_REGION")

    if (
        GCP_DATAFLOW_SERVICE_ACCOUNT_EMAIL is None
        or GCP_DATAFLOW_MACHINE_TYPE is None
        or GCP_DATAFLOW_TEMP_LOCATION is None
        or GCP_DATAFLOW_STAGING_LOCATION is None
        or GCP_DATAFLOW_REGION is None
    ):
        raise ValueError("Dataflow configuration is missing")

    return DataflowConfig(
        region=GCP_DATAFLOW_REGION,
        service_account=GCP_DATAFLOW_SERVICE_ACCOUNT_EMAIL,
        machine_type=GCP_DATAFLOW_MACHINE_TYPE,
        temp_location=GCP_DATAFLOW_TEMP_LOCATION,
        staging_location=GCP_DATAFLOW_STAGING_LOCATION,
    )


def get_dataflow_client() -> dataflow.FlexTemplatesServiceClient:
    return dataflow.FlexTemplatesServiceClient()


def launch_run(
    template_file_gcs_location: str,
    image: str,
    module_name: str,
    data_sources: dict,
    output_path: str,
    components_path: str = "/opt/dependencies/",
    dataflow_client=Depends(get_dataflow_client),
    config=Depends(get_dataflow_config),
):
    pass


#     gcloud dataflow flex-template run "test-run-`date +%Y%m%d-%H%M%S`" \
#     --template-file-gcs-location "gs://vulkan-dev-user-resources/build-assets/flex-template/${POLICY_ID}.json" \
#     --parameters image="us-central1-docker.pkg.dev/vulkan-dev-a8b0/docker-images/${POLICY_ID}:beam" \
#     --parameters output_path="gs://vulkan-dev-beam-results/test/policy_id" \
#     --parameters data_sources='{"input_node": "gs://vulkan-dev-upload-service-bucket/data/e385da7c-b5de-4bd5-85e5-f30897a79aee/1d909f6a-37a4-4cc2-bf48-09e3ce4d1b5d"}' \
#     --parameters module_name="test_policy" \
#     --parameters components_path="/opt/dependencies/"
