# Azure MLOps project

This project intended to show a complete ml pipeline for azure with python.

### Usage
For local development:
1.  Create .env file in the root of the repository with the variables from env_example, where:
  - ENV_NAME= the name of the resource group in azure where project will be run

  - WORKSPACE_PATH= path to the repository root

  - AZURE_PATH= path to .azure folder with azure credentials

  - DEPLOY_API_KEY= api key to fetch data from https://financialmodelingprep.com

  - SUBSCRIPTIONID= azure subscription id to use

  - REGION= resource group location

  - STORAGEACCOUNTNAME= name of the storage account where tfstate container is placed

2. You can start docker container by running:
- ```shell
  docker compose up

- jupyter notebook will start at http://127.0.0.1/lab
3. Or for local interpreter:
- ```shell
  poetry install

4. To deploy on azure run make commands:
```shell
make create_rg
make deploy
make export_requirements
make register_azure
```

5. You can run on local machine - head over to notebooks/local.ipynb
6. To run on azure - download config.json from azure ml studio and place it in the root of the repository
7. Then head over to notebooks/pipeline.ipynb

8. To delete everything from azure run make command:
```shell
make delete_rg
```