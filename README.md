# Azure MLOps project

This project intended to show a complete ml pipeline for azure with python.
Neural network trained to predict stock prices.

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

  - CONTAINERNAME= name of the container for terraform state file

2. In the infrastructure folder create .conf and .tfvars files in configs and variables folder with the name of resource group you are using
3. You can start docker container by running:
- ```shell
  docker compose up

- jupyter notebook will start at http://127.0.0.1/lab
4. Or for local interpreter:
- ```shell
  poetry install

5. To deploy on azure run make commands:
```shell
make create_rg
make deploy
make export_requirements
make register_azure
```

6. To deploy with azure devops:
    - In azure devops create a service connection with the name of subscription id
    - Install terraform extension from marketplace
    - Azure devops pipelines files located in the infrastructure folder (create.yaml and delete.yaml)
7. You can run on local machine - head over to notebooks/local.ipynb
8. To run on azure - download config.json from azure ml studio and place it in the root of the repository
9. Then head over to notebooks/pipeline.ipynb

10. To delete everything from azure run make command:
```shell
make delete_rg
```