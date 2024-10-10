from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from alphonse.models import models

SYSTEM_PROMPT = """
You are an assistant in charge of validate if the information provided is enough to start analyzing a case.
You will have some cases where you have to check if in the provided information (JSON format) you have the necessary information to start the analysis.
- Store not showing problem: Check for store_id

If the information is not enough, return a JSON with the key "missing_information" with true, or false if the information is enough and in the key "description" should tell what is the information missed.
The required information is not always as key in the JSON format, it could be on the other keys so you have to anayze en extract the information if it is in any part of the JSON.
You have to look for the required information in any of the keys of the JSON, for example if we need an ID it may not be as key "id" but it can be in the description, the title, or any other field.
If the information is related to another problem that is not the specified, the key "description" should tell 'Information provided is related to another problem'
Have in mind that the input data could be written in spanish or english.
"""  # noqa

validation_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        (
            "user",
            "This is the information {input_data} for the problem {problem_type}",  # noqa
        ),
    ]
)

validation_chain = validation_prompt | models.gpt4o | JsonOutputParser()
