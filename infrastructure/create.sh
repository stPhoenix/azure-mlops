#!/bin/bash

# Add this line to make the script exit on any command failure
set -e

# Check if the Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo "Azure CLI is not installed. Please install it before running this script."
    exit 1
fi


# Assign input parameters to variables
resourceGroupName=$ENV_NAME
subscriptionId=$SUBSCRIPTIONID
location=$REGION
storageAccountName=$STORAGEACCOUNTNAME

# Log in to Azure (if not already logged in)
az account show 1>/dev/null 2>&1
if [ $? -ne 0 ]; then
    az login
fi

# Get the Object ID of the currently signed-in user
currentUserId=$(az ad signed-in-user show --query id)
# Remove quotes from currentUserId
currentUserId=$(sed -e 's/^"//' -e 's/"$//' <<< "$currentUserId")

# Set the active subscription
az account set --subscription $subscriptionId

# Create the resource group
az group create --name $resourceGroupName --location $location

echo "Resource group '$resourceGroupName' created"

# Create the storage account
az storage account create --name $storageAccountName \
                          --resource-group $resourceGroupName \
                          --location $location \
                          --sku Standard_LRS \
                          --kind StorageV2

echo "Storage account '$storageAccountName' created."

# Create container for terraform state
az storage container create -n ml-tfstate --account-name $storageAccountName

echo "Container for terraform state created"

# Assign the Owner role to the currently signed-in user over the resource group
az role assignment create --assignee $currentUserId --role "Owner" --resource-group $resourceGroupName
az role assignment create --assignee $currentUserId --role "Storage Blob Data Contributor" --scope /subscriptions/$subscriptionId/resourceGroups/$resourceGroupName/providers/Microsoft.Storage/storageAccounts/$storageAccountName


