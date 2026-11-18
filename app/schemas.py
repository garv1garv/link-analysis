from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional


class LinkAnalysisRequest(BaseModel):
    url: HttpUrl = Field(
        ...,
        description="Valid website URL to analyze",
        json_schema_extra={"example": "https://example.com"},
    )


# --- Brand Summary ---
class BrandSummary(BaseModel):
    name: str = Field(..., description="Brand name extracted or inferred from website")
    category: str = Field(..., description="Main business category or industry")
    summary: str = Field(..., description="Short business summary")


# --- Section 1: Competitor Analysis ---
class CompetitorItem(BaseModel):
    name: str = Field(..., description="Competitor brand name")
    main_service: str = Field(..., description="Primary service or offering of competitor")
    target_market: Optional[str] = Field(None, description="Target customer segment")
    strengths: str = Field(..., description="Key competitor strengths")
    gaps_weaknesses: str = Field(..., description="Competitor weaknesses or gaps in offering")


class CompetitorAnalysis(BaseModel):
    brand_overview: str = Field(..., description="Your brand's comprehensive overview")
    main_business_category: str = Field(..., description="Main business category")
    main_products_services: List[str] = Field(..., description="List of main products and services")
    competitors: List[CompetitorItem] = Field(..., min_length=3, description="Identified competitors (minimum 3)")
    brand_competitive_advantages: List[str] = Field(..., description="Your brand's unique competitive advantages")
    market_positioning_opportunities: List[str] = Field(..., description="Opportunities to improve market positioning")


# --- Section 2: Target Search Queries ---
class TargetSearchQuery(BaseModel):
    query: str = Field(..., description="Target search query")
    platforms: List[str] = Field(
        ...,
        description="Relevant platforms from: Google, Facebook, Instagram, LinkedIn, X",
        json_schema_extra={"example": ["Google", "LinkedIn"]},
    )
    search_intent: str = Field(..., description="Search intent (e.g. Service Search, B2B, Discovery)")
    business_relevance: str = Field(..., description="Why this query is relevant to the business")
    target_audience: str = Field(..., description="Target customer segment for this query")


# --- Section 3: SEO Improvement ---
class SEOImprovements(BaseModel):
    primary_keyword: str = Field(..., description="Primary SEO target keyword")
    secondary_keywords: List[str] = Field(..., description="List of secondary keywords")
    long_tail_keywords: List[str] = Field(..., description="List of high-intent long-tail keywords")
    relevant_business_keywords: List[str] = Field(..., description="Additional relevant business keywords")
    recommended_title: str = Field(..., description="Optimized SEO Title (< 60 chars)")
    meta_description: str = Field(..., description="Human-friendly meta description (< 160 chars)")
    supporting_content: List[str] = Field(
        ...,
        description="Content suggestions (e.g. landing pages, blog topics, FAQs, industry pages)",
    )


# --- Section 4: Top 5 Services ---
class ServiceItem(BaseModel):
    service_name: str = Field(..., description="Name of the service")
    description: str = Field(..., description="Short service explanation grounded in website content")
    target_industry: str = Field(..., description="Relevant business industry")
    target_customer: str = Field(..., description="Potential customer type")
    main_benefit: str = Field(..., description="Why customers need this service")


# --- Section 5: Target Audience Identification ---
class AudienceSegment(BaseModel):
    audience: str = Field(..., description="Audience label (e.g. Audience 1: Small Businesses)")
    business_type: str = Field(..., description="Business or user type")
    requirement: str = Field(..., description="Core requirement or need")


class TargetAudience(BaseModel):
    primary_audience: List[str] = Field(..., description="Primary target audience groups")
    secondary_audience: List[str] = Field(..., description="Secondary target audience groups")
    industry_segments: List[str] = Field(..., description="Specific industry segments served")
    business_types: List[str] = Field(..., description="Types of businesses or consumers targeted")
    customer_profiles: List[str] = Field(..., description="Ideal customer profile descriptions")
    location_geographical_focus: Optional[str] = Field(None, description="Geographical focus if available/applicable")
    customer_needs_challenges: List[str] = Field(..., description="Customer pain points, needs, and challenges")
    potential_customer_interests: List[str] = Field(..., description="Customer interests and affinities")
    recommended_marketing_segments: List[AudienceSegment] = Field(
        ...,
        description="Structured audience segments for marketing campaigns",
    )


# --- Complete Aggregated Analysis ---
class FullAnalysis(BaseModel):
    competitor_analysis: CompetitorAnalysis
    target_search_queries: List[TargetSearchQuery] = Field(..., min_length=5, max_length=5)
    seo_improvements: SEOImprovements
    top_services: List[ServiceItem] = Field(..., min_length=3, max_length=5)
    target_audience: TargetAudience


class LinkAnalysisResponse(BaseModel):
    success: bool = True
    website: str
    brand: BrandSummary
    analysis: FullAnalysis
