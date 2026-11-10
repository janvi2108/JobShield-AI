"""JobShield AI — Job Posting Extraction Schemas.

Defines Pydantic request and response models for URL-based and text-based
job posting extraction, field normalization, and completeness scoring.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict, model_validator


class UrlExtractionRequest(BaseModel):
    url: str = Field(..., min_length=8, max_length=2000, description="Publicly accessible job posting URL")


class TextExtractionRequest(BaseModel):
    text: str = Field(..., min_length=20, max_length=100000, description="Raw job description text or copied portal posting")


class ExtractedJobData(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    title: Optional[str] = Field(default=None, description="Extracted job title")
    company_name: Optional[str] = Field(default=None, description="Hiring organization / company name")
    company_profile: Optional[str] = Field(default=None, description="Company background / profile")
    company_description: Optional[str] = Field(default=None, description="Company background / profile (synonym)")
    description: Optional[str] = Field(default=None, description="Comprehensive job description text")
    location: Optional[str] = Field(default=None, description="Geographic location or city/state/country")
    is_remote: Optional[bool] = Field(default=None, description="True if telecommuting / remote, False if on-site")
    telecommuting: Optional[bool] = Field(default=None, description="Telecommuting flag compatible with model")
    work_arrangement: Optional[str] = Field(default=None, description="Work arrangement: Hybrid, Remote, or On-site")
    duration: Optional[str] = Field(default=None, description="Internship or contract duration (e.g. 6 months)")
    employment_type: Optional[str] = Field(default=None, description="Full-time, Part-time, Contract, Temporary, Internship, etc.")
    is_internship: Optional[bool] = Field(default=None, description="True if internship/trainee, False if regular full/part-time")
    salary_range: Optional[str] = Field(default=None, description="Compensation, hourly rate, or stipend range")
    compensation: Optional[str] = Field(default=None, description="Formatted compensation or stipend description")
    required_experience: Optional[str] = Field(default=None, description="Experience level (e.g. Entry level, Mid-Senior, 2+ years)")
    required_education: Optional[str] = Field(default=None, description="Education requirement (e.g. Bachelor's, High School, Unspecified)")
    required_skills: List[str] = Field(default_factory=list, description="Extracted technical and professional skills")
    responsibilities: Optional[str] = Field(default=None, description="Summary of core duties and responsibilities")
    requirements: Optional[str] = Field(default=None, description="Qualifications and candidate prerequisites")
    benefits: Optional[str] = Field(default=None, description="Offered perks, insurance, stipends, or benefits")
    application_instructions: Optional[str] = Field(default=None, description="How to apply / submission steps")
    contact_email: Optional[str] = Field(default=None, description="Contact email address extracted from posting")
    contact_phone: Optional[str] = Field(default=None, description="Contact phone or messaging number")
    contact_info: Optional[str] = Field(default=None, description="Alternative contact details (phone, chat handle, telegram)")
    application_url: Optional[str] = Field(default=None, description="Official career portal URL if detected in text")
    has_company_logo: Optional[bool] = Field(default=None, description="True if verified logo is present")
    has_questions: Optional[bool] = Field(default=None, description="True if application screening questions exist")
    registration_fee_mentioned: Optional[bool] = Field(default=False, description="True if application/training fee is mentioned")
    fee_details: Optional[str] = Field(default=None, description="Details of any upfront payment demand if found")
    suspicious_claims: List[str] = Field(default_factory=list, description="Explicit suspicious claims (guarantees, wire transfer, etc.)")

    # Completeness and metadata
    completeness_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Ratio of populated core attributes (0.0 to 1.0)")
    missing_fields: List[str] = Field(default_factory=list, description="List of expected fields that could not be found")

    @model_validator(mode="after")
    def sync_field_synonyms(self) -> ExtractedJobData:
        """Synchronize synonyms between company_profile/description and remote flags."""
        if self.company_profile and not self.company_description:
            self.company_description = self.company_profile
        elif self.company_description and not self.company_profile:
            self.company_profile = self.company_description

        if self.is_remote is not None and self.telecommuting is None:
            self.telecommuting = self.is_remote
        elif self.telecommuting is not None and self.is_remote is None:
            self.is_remote = self.telecommuting

        if self.contact_phone and not self.contact_info:
            self.contact_info = self.contact_phone
        elif self.contact_info and not self.contact_phone:
            self.contact_phone = self.contact_info

        if self.salary_range and not self.compensation:
            self.compensation = self.salary_range
        elif self.compensation and not self.salary_range:
            self.salary_range = self.compensation

        if self.work_arrangement:
            w_lower = self.work_arrangement.lower()
            if "remote" in w_lower or "telecommuting" in w_lower:
                self.is_remote = True
                self.telecommuting = True
            elif "hybrid" in w_lower:
                self.is_remote = False
                self.telecommuting = False
            elif "on-site" in w_lower or "office" in w_lower:
                self.is_remote = False
                self.telecommuting = False

        return self


class CompletenessInfo(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    score: int = Field(default=0, ge=0, le=100, description="Completeness percentage from 0 to 100")
    missing_fields: List[str] = Field(default_factory=list, description="List of missing attributes")


class ExtractionResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    success: bool = Field(default=True, description="Indicates whether extraction succeeded")
    is_valid_job: bool = Field(default=True, description="False if input content was identified as non-job technical data")
    validation_message: Optional[str] = Field(default=None, description="Actionable notice if input fails job content validation")
    invalid_signals: List[str] = Field(default_factory=list, description="Specific non-job indicators detected")
    source_type: str = Field(default="text", description="'url' or 'text'")
    extraction_method: str = Field(default="text", description="'url' or 'text'")
    source_identifier: str = Field(default="", description="Source URL or text snippet")
    extracted_job: ExtractedJobData = Field(description="Canonical extracted job data object")
    extracted_data: ExtractedJobData = Field(description="Alias pointing to extracted job data for backwards compatibility")
    completeness: CompletenessInfo = Field(default_factory=CompletenessInfo, description="Completeness score and missing attributes")
    extraction_confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Dynamic confidence score from 0.0 to 1.0")
    raw_character_count: int = Field(default=0, description="Length of raw HTML or input text")
    cleaned_character_count: int = Field(default=0, description="Length of cleaned content after parsing")
    warnings: List[str] = Field(default_factory=list, description="Extraction notices or warnings")
    extraction_time_seconds: float = Field(default=0.0, description="Time taken to extract and normalize data")
    # Extraction status enum — backward-compatible (defaults to SUCCESS for existing consumers)
    # Possible values: SUCCESS, PARTIAL_EXTRACTION, ACCESS_RESTRICTED, JAVASCRIPT_REQUIRED,
    #                  LISTING_PAGE, NOT_A_JOB_POSTING, RETRIEVAL_FAILED, URL_INVALID
    extraction_status: str = Field(default="SUCCESS", description="Machine-readable status code for the extraction attempt")
