ARG BASE_IMAGE_NAME
FROM ${BASE_IMAGE_NAME}

ENV FLEX_TEMPLATE_PYTHON_PY_FILE="/opt/dependencies/vulkan/vulkan/beam/metrics/pipeline.py"

# Set the entrypoint to Apache Beam SDK launcher.
ENTRYPOINT ["/opt/apache/beam/boot"]
