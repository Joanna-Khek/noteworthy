FROM python:3.11-slim

ARG DEBIAN_FRONTEND="noninteractive"

ARG NON_ROOT_USER="aisg"
ARG NON_ROOT_UID="2222"
ARG NON_ROOT_GID="2222"
ARG HOME_DIR="/home/${NON_ROOT_USER}"

ARG REPO_DIR="."

RUN useradd -l -m -s /bin/bash -u ${NON_ROOT_UID} ${NON_ROOT_USER}

RUN apt update && \
    apt -y install curl git && \
    apt clean

ENV PYTHONIOENCODING utf8
ENV LANG "C.UTF-8"
ENV LC_ALL "C.UTF-8"
ENV PATH "./.local/bin:${PATH}"

USER ${NON_ROOT_USER}
WORKDIR ${HOME_DIR}

COPY --chown=${NON_ROOT_USER}:${NON_ROOT_GID} ${REPO_DIR}/requirements.txt noteworthy/requirements.txt

# Install pip requirements
RUN pip install -r noteworthy/requirements.txt

COPY --chown=${NON_ROOT_USER}:${NON_ROOT_GID} ${REPO_DIR} noteworthy

WORKDIR ${HOME_DIR}/noteworthy

# Expose port
EXPOSE 8501

RUN chmod -R 777 .

# Run streamlit command
CMD ["python", "-m", "streamlit", "run", "app/Home.py"]