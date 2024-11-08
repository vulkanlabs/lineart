ARG PYTHON_VERSION="3.12"
FROM python:${PYTHON_VERSION}

ARG VULKAN_HOME
ARG VULKAN_SERVER_PATH
ARG VULKAN_STAGING_PATH
ARG VULKAN_SCRIPTS_PATH
ARG VULKAN_VENVS_PATH
ENV VULKAN_HOME=${VULKAN_HOME}
ENV VULKAN_SERVER_PATH=${VULKAN_SERVER_PATH}
ENV VULKAN_STAGING_PATH=${VULKAN_STAGING_PATH}
ENV VULKAN_LIB_PATH=${VULKAN_STAGING_PATH}/lib
ENV VULKAN_SCRIPTS_PATH=${VULKAN_SCRIPTS_PATH}
ENV VULKAN_VENVS_PATH=${VULKAN_VENVS_PATH}

RUN mkdir ${VULKAN_HOME}
RUN mkdir ${VULKAN_VENVS_PATH}
RUN mkdir ${VULKAN_STAGING_PATH}

EXPOSE 6002

WORKDIR ${VULKAN_SERVER_PATH}

RUN pip install uv
RUN uv pip install --system build

COPY vulkan-public vulkan-public
COPY vulkan vulkan
COPY beam-launcher beam-launcher/
RUN uv pip install --system --no-cache beam-launcher/

RUN python -m build vulkan --outdir ${VULKAN_LIB_PATH} --sdist
RUN python -m build vulkan-public --outdir ${VULKAN_LIB_PATH} --sdist

ENTRYPOINT ["fastapi", "dev" , "beam-launcher/server/app.py", "--host", "0.0.0.0", "--port", "6002", "--no-reload"]