import marvin

from .openai import OpenAIChatLLM


class AzureOpenAIChatLLM(OpenAIChatLLM):
    model: str = "gpt-35-turbo-0613"

    def _get_openai_settings(self) -> dict:
        # do not load the base openai settings; any azure settings must be set
        # explicitly
        openai_kwargs = {}

        if marvin.settings.azure_openai.api_key:
            openai_kwargs["api_key"] = (
                marvin.settings.azure_openai.api_key.get_secret_value()
            )
        else:
            raise ValueError(
                "Azure OpenAI API key not set. Please set it or use the"
                " MARVIN_AZURE_OPENAI_API_KEY environment variable."
            )
        if marvin.settings.azure_openai.deployment_name:
            openai_kwargs["deployment_id"] = (
                marvin.settings.azure_openai.deployment_name
            )
        if marvin.settings.azure_openai.api_type:
            openai_kwargs["api_type"] = marvin.settings.azure_openai.api_type
        if marvin.settings.azure_openai.api_base:
            openai_kwargs["api_base"] = marvin.settings.azure_openai.api_base
        if marvin.settings.azure_openai.api_version:
            openai_kwargs["api_version"] = marvin.settings.azure_openai.api_version
        return openai_kwargs