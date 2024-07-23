ARG APP_DIR=/app

FROM python:3.10-slim AS builder
# source the argument
ARG APP_DIR

# install
# it's important to run this all together
# otherwise the released memory via rm -rf won't be reflected in the image
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y \
    curl \
    build-essential \
    libffi-dev && \
    rm -rf /var/lib/apt/lists/*

# set up poetry to it is installed properly and cleanly
ENV POETRY_VERSION="1.8.3"
ENV POETRY_HOME="/opt/poetry"
# install poetry into the builder image
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH=${POETRY_HOME}/bin:${PATH}

WORKDIR ${APP_DIR}
# creates the virtual environment using venv and copies the files (not symlinks)
RUN python -m venv ${APP_DIR}/venv --copies
# copy over the poetry files
COPY poetry.lock pyproject.toml ./
# activate the virtual environment and install the dependencies via poetry (with only main dependencies)
RUN . ${APP_DIR}/venv/bin/activate \
    && poetry install --only main


FROM python:3.10-slim AS deploy
ARG APP_DIR

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR ${APP_DIR}
# copy over the virtual environment from the builder image
COPY --from=builder ${APP_DIR}/venv ${APP_DIR}/venv
# add the python virtual environment to the path
ENV PATH=${APP_DIR}/venv/bin:${PATH}

# copy over the current directory (our current code) to the app directory
COPY . .
# delete the data directory, as it is not needed in the image
RUN rm -rf ./data

CMD ["uvicorn", "src.server.main:app", "--host", "0.0.0.0", "--port", "8000"]

# health checks are not needed, as kubenetes uses liveness and readiness probes
