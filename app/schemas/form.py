# app/schemas/form.py
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FormTemplateBase(BaseModel):
    name: str
    description: Optional[str] = None
    schema_: dict = Field(default_factory=dict, alias="schema")
    active: bool = True
    stay_active_after_submission: bool = True
    booking_type_id: Optional[UUID] = None

    model_config = ConfigDict(populate_by_name=True)


class FormTemplateCreate(FormTemplateBase):
    pass


class FormTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    schema_: Optional[dict] = Field(None, alias="schema")
    active: Optional[bool] = None
    stay_active_after_submission: Optional[bool] = None
    booking_type_id: Optional[UUID] = None

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class FormTemplateOut(BaseModel):
    id: UUID
    workspace_id: UUID
    name: str
    description: Optional[str] = None
    schema_: dict = Field(alias="schema")
    active: bool
    stay_active_after_submission: bool
    booking_type_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class FormSubmissionOut(BaseModel):
    id: UUID
    form_template_id: UUID
    booking_id: UUID
    contact_id: UUID
    submitted_at: datetime
    answers: dict
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PublicFormSubmitRequest(BaseModel):
    template_id: UUID
    booking_id: UUID
    contact_id: UUID
    answers: dict = {}

    model_config = ConfigDict(extra="forbid")


class PublicContactRequest(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    message: Optional[str] = None

    model_config = ConfigDict(extra="forbid")
