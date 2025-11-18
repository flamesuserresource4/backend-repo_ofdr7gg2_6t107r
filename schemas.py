"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- LeadJob -> "leadjob" collection
- Lead -> "lead" collection
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List


class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: Optional[str] = Field(None, description="Full name")
    email: EmailStr = Field(..., description="Email address")
    password_hash: Optional[str] = Field(None, description="Hashed password (if email/password signup)")
    auth_provider: str = Field("password", description="Auth provider: password | google")
    is_active: bool = Field(True, description="Whether user is active")


class LeadJob(BaseModel):
    """
    Lead generation job request
    Collection name: "leadjob"
    """
    user_id: Optional[str] = Field(None, description="User ID who requested the job")
    location: str = Field(..., description="Target location")
    job_title: str = Field(..., description="Target job title")
    company_size_range: str = Field(..., description="Company size range, e.g., 11-50, 51-200")
    industry_keywords: List[str] = Field(..., description="List of industry keywords")
    status: str = Field("processing", description="Job status: processing | ready | failed")
    result_count: int = Field(0, description="Number of leads generated")


class Lead(BaseModel):
    """
    Leads collection schema
    Collection name: "lead"
    """
    job_id: str = Field(..., description="Associated LeadJob ID")
    name: str = Field(..., description="Contact name")
    email: Optional[EmailStr] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    linkedin: Optional[str] = Field(None, description="LinkedIn URL")
    company: str = Field(..., description="Company name")
    title: str = Field(..., description="Job title")
    location: str = Field(..., description="Location")
    company_size: str = Field(..., description="Company size bucket")
    industry: Optional[str] = Field(None, description="Industry or keyword match")
