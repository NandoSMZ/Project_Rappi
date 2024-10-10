import requests
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from loguru import logger
from alphonse.config import settings
from alphonse.models import models


def fetch_data(endpoint_template, **kwargs):
    """
    Fetch data from an API endpoint with a formatted URL.

    Args:
        base_url (str): The base URL for the API.
        endpoint_template (str): The endpoint URL template
        **kwargs: Variables to format the endpoint URL.

    Returns:
        dict: The JSON response from the API.

    Raises:
        ValueError: If the request to the API fails.
    """
    url = settings.ms_base_url + endpoint_template.format(**kwargs)
    response = requests.get(url, timeout=10)
    if response.status_code == 200:
        return response.json()
    raise ValueError(f"Error in the request to the API: {response.text}")


def extract_data_from_input(input_data: dict, prompt: str) -> dict:
    """
    Chain that extracts data from the input data based on the provided keys.

    Args:
        input_data (dict): The information to extract data from.
        data_keys (list): The keys to extract from the input data.

    Returns:
        dict: The extracted data.
    """
    extraction_prompt = ChatPromptTemplate.from_template(prompt)
    extraction_chain = extraction_prompt | models.gpt4o | JsonOutputParser()
    extraction_result = extraction_chain.invoke({"input_data": input_data})
    logger.debug(f"Extraction result: {extraction_result}")
    return extraction_result

country_name = {
    "MX": "Mexico",
    "CO": "Colombia",
    "AR": "Argentina",
    "CL": "Chile",
    "PE": "Peru",
    "UY": "Uruguay",
    "EC": "Ecuador",
    "CR": "Costa Rica",
    "BR": "Brazil"
}
def get_country_name(country: str) -> str:
    return country_name.get(country.upper(), "Colombia")

def get_lenguage(country: str) -> str:
    """
    Get the language based on the country.

    Args:
        country (str): The country to get the language from.

    Returns:
        str: The language code.
    """
    if country.upper() in ["MX", "CO", "AR", "CL", "PE", "UY", "EC", "CR"]:
        return "Spanish"
    elif country.upper() in ["BR"]:
        return "Portuguese"
    else:
        return "English"

def compare_data(
    input_data: dict,
    comparison_data: dict,
    system_prompt: str,
    user_prompt: str,
    response_language: str = "Spanish",
    current_date: str = None,
    current_day: str = None,
    country_name: str = None,
    typification_dict: dict = None,
    return_input_prompt: bool = False,
) -> dict:
    """
    Chain that compares the input data with the comparison data.

    Args:
        input_data (dict): The input data to compare.
        comparison_data (dict): The data to compare with.
        prompt (str): The prompt to use for comparison.

    Returns:
        dict: The comparison result.
    """
    comparison_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("user", user_prompt),
        ]
    )
    comparison_chain = comparison_prompt | models.gpt3 | JsonOutputParser()
    comparison_result = comparison_chain.invoke(
        {"input_data": input_data,"comparison_data": comparison_data, "response_language": response_language,
         "current_date": current_date, "current_day": current_day, "country_name": country_name, "typification_dict": typification_dict}
    )
    logger.debug(f"Comparison result: {comparison_result}")
    if return_input_prompt:
        return {
            "comparison_result": comparison_result,
            "input_prompt": comparison_prompt.format(
                input_data=input_data, comparison_data=comparison_data, response_language= response_language,
                current_date=current_date, current_day=current_day, country_name=country_name, typification_dict=typification_dict
            ),
        }
    return comparison_result
