ARG PYTHON_VERSION
ARG BEAM_SDK_VERSION
ARG FLEX_TEMPLATE_BASE_IMAGE

FROM python:${PYTHON_VERSION}-slim

# Copy files from official SDK image, including script/dependencies.
COPY --from=apache/beam_python${PYTHON_VERSION}_sdk:${BEAM_SDK_VERSION} /opt/apache/beam /opt/apache/beam

# Copy Flex Template launcher binary from the launcher image, which makes it
# possible to use the image as a Flex Template base image.
COPY --from=${FLEX_TEMPLATE_BASE_IMAGE} /opt/google/dataflow/python_template_launcher /opt/google/dataflow/python_template_launcher

RUN pip install uv --no-cache-dir

RUN mkdir /opt/dependencies
COPY /workspace/vulkan /opt/dependencies/vulkan
COPY /workspace/vulkan-public /opt/dependencies/vulkan-public

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
