ARG _BEAM_BASE_IMAGE
FROM ${_BEAM_BASE_IMAGE}

ENV FLEX_TEMPLATE_PYTHON_PY_FILE="/opt/dependencies/vulkan/vulkan/beam/metrics/pipeline.py"

# Set the entrypoint to Apache Beam SDK launcher.
ENTRYPOINT ["/opt/apache/beam/boot"]
