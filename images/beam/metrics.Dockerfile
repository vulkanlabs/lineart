ARG PYTHON_VERSION="3.12"
ARG BEAM_SDK_VERSION="2.60.0"
ARG FLEX_TEMPLATE_BASE_IMAGE="gcr.io/dataflow-templates-base/python312-template-launcher-base:public-image-latest"

# Copy files from official SDK image, including script/dependencies.
FROM apache/beam_python${PYTHON_VERSION}_sdk:${BEAM_SDK_VERSION} AS beam_base
# Copy Flex Template launcher binary from the launcher image, which makes it
# possible to use the image as a Flex Template base image.
FROM ${FLEX_TEMPLATE_BASE_IMAGE} AS flex_template_base

FROM python:${PYTHON_VERSION}-slim
COPY --from=beam_base /opt/apache/beam /opt/apache/beam
COPY --from=flex_template_base /opt/google/dataflow/python_template_launcher /opt/google/dataflow/python_template_launcher

RUN pip install uv --no-cache-dir
RUN mkdir /opt/dependencies
COPY vulkan /opt/dependencies/vulkan
COPY vulkan-public /opt/dependencies/vulkan-public

# TODO: This is a workaround to ensure vulkan dependencies are installed
RUN uv pip install --system --no-cache --extra beam -r /opt/dependencies/vulkan/pyproject.toml
RUN uv pip install --system --no-cache \    
    /opt/dependencies/vulkan-public \
    /opt/dependencies/vulkan 

# Location to store the pipeline artifacts.
WORKDIR /template
COPY launch_dataflow.py /template/launch_dataflow.py

ENV FLEX_TEMPLATE_PYTHON_PY_FILE="/template/launch_dataflow.py"

# Set the entrypoint to Apache Beam SDK launcher.
ENTRYPOINT ["/opt/apache/beam/boot"]
