.PHONY: help

WORKDIR := $(shell pwd)
.ONESHELL:
.EXPORT_ALL_VARIABLES:

ifneq ("$(wildcard .env)","")
    include .env
    export $(shell sed 's/=.*//' .env)
    ENV_FILE?=$(WORKDIR)/.env
else
endif

api-key ?= ${DEPLOY_API_KEY}


help:
	@echo "Available commands:"
	@echo ""
	@grep -E '^([a-zA-Z_-]+):.*## (.+)' $(MAKEFILE_LIST) | awk -F '## ' '{printf "%-20s %s\n", $$1, $$2}'

init: ## Init terraform
	@cd ./infrastructure && \
		terraform init -backend-config="configs/$(ENV_NAME)_backend.conf" -reconfigure -upgrade

deploy: ## Deploy terraform
	@$(MAKE) init
	@cd ./infrastructure && \
		terraform apply -var-file=variables/$(ENV_NAME).tfvars -var="api-key=$(api-key)" -auto-approve

validate: ## Validate terraform
	@$(MAKE) init
	@cd ./infrastructure && \
		terraform validate

plan: ## Plan terraform
	@$(MAKE) init
	@cd ./infrastructure && \
		terraform plan -var-file=variables/$(ENV_NAME).tfvars -var="api-key=$(api-key)"

destroy: ## Destroy terraform
	@$(MAKE) init
	@cd ./infrastructure && \
		terraform destroy -var-file=variables/$(ENV_NAME).tfvars -var="api-key=$(api-key)"

create_rg: ## Create infrastructure for terraform state
	@cd ./infrastructure && bash create.sh

delete_rg: ## Delete all infrastructure
	@cd ./infrastructure && bash delete.sh

export_requirements: ## Export requirements from poetry to requirements.txt
	@poetry export -f requirements.txt -o src/stockpredict/docker-contexts/default/requirements.txt --without=dev
	@echo "Requirements exported to txt"

register_azure: ## Register components in azure ml
	@cd ./infrastructure && bash register_azure.sh