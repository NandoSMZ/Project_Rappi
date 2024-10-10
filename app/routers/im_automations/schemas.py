""" This module contains the schemas for the
Incident Management automation endpoints. """

from typing import Optional, Any

from pydantic import BaseModel


class BaseProblemRequestBody(BaseModel):
    """
    Schema for the request body of the base problem endpoint.
    """

    ticket_title: str
    ticket_description: str
    extra_information: Optional[dict[Any, Any]] = None


class StoreNotShowingRequestBody(BaseProblemRequestBody):
    """
    Schema for the request body of the store not showing problem endpoint.
    """

    country: str
    vertical: str
    store_id: Optional[str] = None
    address: Optional[str] = None
    user_id: Optional[str] = None


class AutomationResponseBody(BaseModel):
    """
    Schema for the response body of the store not showing problem endpoint.
    """

    problem_type: Optional[str] = None
    description: str

class AutomationResponseBodyStoreNotFound(AutomationResponseBody):
    """
    Schema for the response body of the store not showing problem endpoint.
    """

    transitions_issue: Optional[str] = None
    typification_issue: Optional[str] = None


class CouponProblemsRequestBody(BaseProblemRequestBody):
    """
    Schema for the request body of the coupon problems endpoint.
    """

    coupon_id: Optional[str] = None


class PortalProblemsRequestBody(BaseProblemRequestBody):
    """
    Schema for the request body of the coupon problems endpoint.
    """

    store_id: Optional[str] = None
    email: Optional[str] = None


class GoProblemsRequestBody(BaseProblemRequestBody):
    """
    Schema for the request body of the Go problem endpoint.
    """

    country: str
    user_id: str
    go_id: str

class ProductProblemsRequestBody(BaseProblemRequestBody):
    """
    Schema for the request body of the product problem endpoint.
    """
    country: str
    store_id: str
    retail_id: str
    email: str
    product_id: str
