set -ex

POLICY_ID=$1
REGION="us-central1"
WORKER_SERVICE_ACCOUNT="beam-worker-service-account@vulkan-dev-a8b0.iam.gserviceaccount.com"
MACHINE_TYPE="n1-standard-2"
GCP_DATAFLOW_TEMP_LOCATION="gs://vulkan-dev-beam-temp"
GCP_DATAFLOW_STAGING_LOCATION="gs://vulkan-dev-beam-temp/staging"

gcloud dataflow flex-template run "test-run-`date +%Y%m%d-%H%M%S`" \
  --template-file-gcs-location "gs://vulkan-dev-user-resources/build-assets/flex-template/${POLICY_ID}.json" \
  --region ${REGION} \
  --service-account-email ${WORKER_SERVICE_ACCOUNT} \
  --temp-location ${GCP_DATAFLOW_TEMP_LOCATION} \
  --staging-location ${GCP_DATAFLOW_STAGING_LOCATION} \
  --worker-machine-type ${MACHINE_TYPE} \
  --parameters image="us-central1-docker.pkg.dev/vulkan-dev-a8b0/docker-images/${POLICY_ID}:beam" \
  --parameters output_path="gs://vulkan-dev-beam-results/test/policy_id" \
  --parameters data_sources='{"input_node": "gs://vulkan-dev-upload-service-bucket/data/e385da7c-b5de-4bd5-85e5-f30897a79aee/1d909f6a-37a4-4cc2-bf48-09e3ce4d1b5d"}' \
  --parameters module_name="test_policy" \
  --parameters components_path="/opt/dependencies/"
