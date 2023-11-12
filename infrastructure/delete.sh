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

# Log in to Azure (if not already logged in)
az account show 1>/dev/null 2>&1
if [ $? -ne 0 ]; then
    az login
fi

# Set the active subscription
az account set --subscription $subscriptionId

# Create the resource group
az group delete --name $resourceGroupName -y

echo "Resource group '$resourceGroupName' deleted"
