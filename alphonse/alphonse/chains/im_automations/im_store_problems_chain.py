import requests
from langchain_core.runnables import chain
from loguru import logger
from alphonse.chains.im_automations import utils
from alphonse.config import settings
from datetime import datetime


SYSTEM_PROMPT = """
You are an assistant that helps with incident management related to store issues within an application.
You will receive a JSON containing various parameters that you must analyze and verify for correctness.
The parameters you need to analyze include:
- storeCreatedAt: The creation date of the store. You will also receive the Current Date {current_date} to help you determine if it has been created less than 8 days ago. If it has been created less than 8 days ago, indicate that it should be searched by category, but is not a problem.
- isEnabled: Whether the store is enabled.
- isOpen: Whether the store is currently open, and it is within the schedules.
- isPublished: Whether the store is published.
- hasExpectedCity: Whether the store's city is as expected.
- hasZones: Whether the store has coverage.
- hasSchedules: Whether the store has configured schedules.
- schedules: An array of schedules, each with a day of the week and a time range. You will also receive the Current Day of the week as {current_day}, the Country as {country_name}, and the current date in UTC. Validate if the current time falls within the configured schedules for the given country.

If multiple parameters are found to be False, prioritize the problems in the following order:
1. isEnabled
2. isPublished
3. hasExpectedCity
4. hasZones
5. isOpen
6. hasSchedules

You must always generate only a JSON response (without additional text just the JSON) with these keys:
- problem_type: Specify the problem you found in the JSON; this could be null if there is no problem.
- description: Write your analysis and explanation of the case, focusing on what is wrong or what was verified.
- transitions_issue: Use the appropriate code ID for the action to be taken. Use `241` if any problem is found, and `161` if there is no problem.
- typification_issue: Use the correct key (Only one) from this dictionary {typification_dict} to determine the correct typification of the issue. If there is no problem, send the string "null".
You will also receive the current date, day of the week, and country as additional parameters to assist in your analysis.
"""

USER_PROMPT = (
    "Taking into account this information {input_data}, proceed with the analysis of the information being returned by the API: {comparison_data}.\n"
    "Examine each parameter in the JSON. If you find a value that indicates a problem, such as a parameter being set to False when it is expected to be True"
    "Remember to be concise and clear in your response, focusing on providing actionable insights. Provide the response in {response_language}."
    "Provide the response in JSON format with the following keys: problem_type, description, transitions_issue, and typification_issue."
)

if "dev" not in settings.ms_base_url.lower():
    BASE_IM_EP_URL = "http://internal-microservices.rappi.com"
else:
    BASE_IM_EP_URL = settings.ms_base_url


def get_input_field(input_data, field, prompt_template):
    """
    Get the value of a field from the input data if it exists, otherwise
    extract the value using the extraction chain.

    Args:
        input_data (dict): The input data
        field (str): The field to get the value from
        prompt_template (str): The prompt to use for the extraction

    Returns:
        str: The value of the field
    """
    value = input_data.get(field)
    if not value:
        logger.debug(f"{field} not found in the input data, extracting it...")
        extraction_result = utils.extract_data_from_input(
            input_data, prompt_template.format(key=field)
        )
        value = extraction_result.get(field)
    return value


@chain
def store_problems_chain(input_data: dict) -> dict:
    """
    Chain that analyzes the information provided by the user and generates a
    response based on the analysis.

    Args:
        input_data (dict): The information to analyze

    Returns:
        dict: The analysis of the information
    """
    typification_dict = {
        "Tienda no visible por partner inactivo": "isEnabled is False or isPublished is False",
        "Tienda no visible por ciudad incorrecta": "hasExpectedCity is False",
        "Zona de cobertura": "hasZones is False",
        "Tienda no visible por falta de horarios": "hasSchedules is False",
        "Tienda fuera de horarios de operación": "current time is outside the configured schedules or isOpen is False",
        "Tienda no registra en el search": "storeCreatedAt is less than 8 days ago",
    }
    DATA_EXTRACTION_PROMPT = (
        "I need you to extract the store_id and email from this information {input_data} and generate a "  # noqa
        "JSON output like this ['{key}': value] where the store_id could be in the title "  # noqa
        "or description, the output should be only the JSON with the key store_id and email"  # noqa
    )
    # Check store data
    country = get_input_field(input_data, "country", DATA_EXTRACTION_PROMPT)
    vertical = get_input_field(input_data, "vertical", DATA_EXTRACTION_PROMPT)
    store_id = get_input_field(input_data, "store_id", DATA_EXTRACTION_PROMPT)
    address = get_input_field(input_data, "address", DATA_EXTRACTION_PROMPT)
    user_id = get_input_field(input_data, "user_id", DATA_EXTRACTION_PROMPT)
    if not country or not vertical or not store_id:
        raise ValueError(
            "There are missing fields in the input "
            + "data to continue with the analysis."
        )
    response_language = utils.get_lenguage(country)
    url = (
        BASE_IM_EP_URL
        + f"/api/im-automations/availability/{vertical}/{country}/{store_id}/{address}/{user_id}"
    )
    automation_ep_res = requests.get(url, timeout=10)
    if automation_ep_res.status_code != 200:
        logger.debug(
            f"Automations EP response code {automation_ep_res.status_code}"
        )
    country_name = utils.get_country_name(country)
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    current_day = datetime.now().strftime("%a").lower()
    logger.debug(f"Information get, Country Name: {country_name}, Date: {current_date}, Day: {current_day}")
    url =  BASE_IM_EP_URL + f"/api/im-automations/availability/{vertical}/{country}/{store_id}/{address}/{user_id}"
    automation_ep_response = requests.get(url, timeout=10)
    if automation_ep_response.status_code != 200:
        logger.debug(f"Automations EP response code {automation_ep_response.status_code}")
        return {
            "problem_type": "store_not_found",
            "description": f"The store_id {store_id} was not found"
            + " in the system, please check the information provided.",
            "transitions_issue": None,
            "typification_issue": None,
        }
    response_dict = automation_ep_res.json()
    llm_response = utils.compare_data(
        input_data, response_dict, SYSTEM_PROMPT, USER_PROMPT, response_language,
        current_date, current_day, country_name, typification_dict, return_input_prompt=True
    )

    if "eval_mode" in input_data and input_data["eval_mode"]:
        return (
            llm_response["comparison_result"]["description"],
            llm_response["input_prompt"],
        )
    else:
        return llm_response["comparison_result"]
