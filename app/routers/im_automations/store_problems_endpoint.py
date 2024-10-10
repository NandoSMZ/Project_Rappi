from fastapi import APIRouter, HTTPException
from loguru import logger

from app.routers.im_automations.schemas import (
    StoreNotShowingRequestBody,
    AutomationResponseBodyStoreNotFound,
)
import alphonse.chains.im_automations as im_automations  # type: ignore

router = APIRouter()


@router.post("/store-problems/")
async def store_problems(
    data: StoreNotShowingRequestBody,
) -> AutomationResponseBodyStoreNotFound:
    """
    Check for problems in the store based on the information provided
    and returns an analysis based on the comparison with the information

    Args:
        data (StoreNotShowingRequestBody): The information to compare and
        analyze by the LLM

    Returns:
        StoreNotShowingResponseBody: Response with the analysis of the
        information
    """
    logger.debug("Validating information")
    validation = im_automations.validation_chain.invoke(
        {"input_data": data, "problem_type": "Store not showing problem"}
    )
    logger.debug(f"Validation result: {validation}")
    if validation["missing_information"]:
        raise HTTPException(status_code=400, detail=validation["description"])
    try:
        logger.debug("Information validated, comparing with API response")
        chain_response = im_automations.store_problems_chain.invoke(
            data.dict()
        )
        response = AutomationResponseBodyStoreNotFound(
            problem_type=chain_response["problem_type"],
            description=chain_response["description"],
            transitions_issue=chain_response["transitions_issue"],
            typification_issue=chain_response["typification_issue"],
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
