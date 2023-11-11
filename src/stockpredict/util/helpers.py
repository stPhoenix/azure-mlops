import asyncio
from asyncio import Future
from typing import Coroutine, Any, Union

import nest_asyncio
from azure.identity import DefaultAzureCredential

nest_asyncio.apply()


def get_api_key(keyvault_name: str, secret_name: str, spark=None) -> str:
    try:
        from azure.keyvault.secrets import SecretClient
        secret_client = SecretClient(vault_url=f"https://{keyvault_name}.vault.azure.net/",
                                     credential=DefaultAzureCredential())
        secret = secret_client.get_secret(secret_name).value
    except ImportError:
        token_library = spark._jvm.com.microsoft.azure.synapse.tokenlibrary.TokenLibrary
        secret = token_library.getSecret(keyvault_name, secret_name)

    return secret


def async_resolver(task: Union[Coroutine, Future]) -> Any:
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(task)

    return result
