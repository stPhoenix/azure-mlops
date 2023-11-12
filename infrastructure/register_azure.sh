#!/bin/bash

# Add this line to make the script exit on any command failure
set -e
set -x

# Check if the Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo "Azure CLI is not installed. Please install it before running this script."
    exit 1
fi


# Assign input parameters to variables
resourceGroupName=$ENV_NAME
subscriptionId=$SUBSCRIPTIONID

workspaceName=$(terraform output workspace-name)
workspaceName=$(sed -e 's/^"//' -e 's/"$//' <<< "$workspaceName")

# Log in to Azure (if not already logged in)
az account show 1>/dev/null 2>&1
if [ $? -ne 0 ]; then
    az login
fi


# Set the active subscription
az account set --subscription $subscriptionId

# Register ml components

cd ../
poetry run register_azure --resource_group $resourceGroupName --workspace_name $workspaceName --subscription_id $subscriptionId
