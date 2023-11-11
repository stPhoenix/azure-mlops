FROM jupyter/pyspark-notebook:python-3.8


USER root
RUN wget https://aka.ms/InstallAzureCLIDeb && bash ./InstallAzureCLIDeb

USER 1000
ENV PYTHONPATH=$PYTHONPATH:/home/jovyan/workspace/src

RUN pip install --upgrade poetry ; poetry config virtualenvs.create false

COPY pyproject.toml /home/jovyan/workspace/pyproject.toml

WORKDIR /home/jovyan/workspace
RUN poetry install
