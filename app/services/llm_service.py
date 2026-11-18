import json
import logging
from typing import Dict, Any
from fastapi import HTTPException, status

from app.config import settings
from app.schemas import FullAnalysis, BrandSummary

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert AI business, competitor, SEO, and market intelligence analyst.
Analyze the provided extracted website content and generate a comprehensive, highly accurate, structured JSON analysis.

CRITICAL INSTRUCTIONS:
1. Ground your analysis strictly in the provided website content. Do not invent unrelated services or features.
2. For Competitors: Identify at least 3 genuine or direct market competitors based on the business category and offerings. If based on AI market inference, ensure they are realistic and clearly relevant.
3. For Search Queries: Return EXACTLY 5 high-impact search queries. Support the 5 platforms (Google, Facebook, Instagram, LinkedIn, X). DO NOT invent search volumes or fake numerical metrics. Specify the query, relevant platforms, search intent, business relevance, and target audience.
4. For SEO Improvements: Suggest actionable primary, secondary, and long-tail keywords, a recommended SEO title (<60 chars), meta description (<160 chars), and supporting content/landing pages.
5. For Top Services: Identify 3 to 5 primary services clearly identified from the website content. Include service name, description, target industry, target customer, and main benefit.
6. For Target Audience: Define primary and secondary audiences, industry segments, business types, customer profiles, geographic focus, pain points/needs, customer interests, and structured marketing segments.
7. Return ONLY valid JSON adhering strictly to the required schema structure without any markdown fencing or extra text.
"""

ANALYSIS_SCHEMA_PROMPT = """
The JSON response must have exactly this structure:
{
  "brand": {
    "name": "Brand Name",
    "category": "Main Category",
    "summary": "Short business summary"
  },
  "competitor_analysis": {
    "brand_overview": "Your brand overview",
    "main_business_category": "Main Category",
    "main_products_services": ["Product/Service 1", "Product/Service 2"],
    "competitors": [
      {
        "name": "Competitor 1",
        "main_service": "Service",
        "target_market": "Market",
        "strengths": "Strengths",
        "gaps_weaknesses": "Gaps"
      },
      {
        "name": "Competitor 2",
        "main_service": "Service",
        "target_market": "Market",
        "strengths": "Strengths",
        "gaps_weaknesses": "Gaps"
      },
      {
        "name": "Competitor 3",
        "main_service": "Service",
        "target_market": "Market",
        "strengths": "Strengths",
        "gaps_weaknesses": "Gaps"
      }
    ],
    "brand_competitive_advantages": ["Advantage 1", "Advantage 2"],
    "market_positioning_opportunities": ["Opportunity 1", "Opportunity 2"]
  },
  "target_search_queries": [
    {
      "query": "query text",
      "platforms": ["Google", "LinkedIn"],
      "search_intent": "Service Search",
      "business_relevance": "Relevance",
      "target_audience": "Audience"
    }
  ],
  "seo_improvements": {
    "primary_keyword": "Primary Keyword",
    "secondary_keywords": ["Secondary 1", "Secondary 2"],
    "long_tail_keywords": ["Long tail 1", "Long tail 2"],
    "relevant_business_keywords": ["Keyword 1", "Keyword 2"],
    "recommended_title": "SEO Title",
    "meta_description": "Meta description",
    "supporting_content": ["Topic 1", "Topic 2"]
  },
  "top_services": [
    {
      "service_name": "Service Name",
      "description": "Description",
      "target_industry": "Industry",
      "target_customer": "Customer",
      "main_benefit": "Benefit"
    }
  ],
  "target_audience": {
    "primary_audience": ["Audience 1"],
    "secondary_audience": ["Audience 2"],
    "industry_segments": ["Segment 1"],
    "business_types": ["Type 1"],
    "customer_profiles": ["Profile 1"],
    "location_geographical_focus": "Global or Region",
    "customer_needs_challenges": ["Need 1"],
    "potential_customer_interests": ["Interest 1"],
    "recommended_marketing_segments": [
      {
        "audience": "Segment A",
        "business_type": "SMB",
        "requirement": "Requirement"
      }
    ]
  }
}
"""


class LLMService:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER.lower()

    async def analyze_website_content(self, scraped_data: Dict[str, Any], url: str) -> Dict[str, Any]:
        """
        Sends extracted website content to LLM (Gemini or OpenAI) and returns structured analysis.
        """
        user_prompt = f"""
WEBSITE URL: {url}
PAGE TITLE: {scraped_data.get('title', 'N/A')}
META DESCRIPTION: {scraped_data.get('meta_description', 'N/A')}
META KEYWORDS: {scraped_data.get('meta_keywords', 'N/A')}
HEADINGS:
{chr(10).join(scraped_data.get('headings', []))}

PAGE CONTENT BODY:
{scraped_data.get('cleaned_text', '')}

{ANALYSIS_SCHEMA_PROMPT}
"""

        if self.provider == "gemini":
            return await self._call_gemini(user_prompt)
        elif self.provider == "openai":
            return await self._call_openai(user_prompt)
        else:
            # Default to gemini if available or fallback
            return await self._call_gemini(user_prompt)

    async def _call_gemini(self, prompt: str) -> Dict[str, Any]:
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="GEMINI_API_KEY is not configured in environment or .env file.",
            )

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(
                api_key=api_key,
                http_options=types.HttpOptions(api_version="v1beta"),
            )
            full_prompt = f"{SYSTEM_PROMPT}\n\n{prompt}"

            response = await client.aio.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                ),
            )
            raw_text = response.text.strip()
            return json.loads(raw_text)

        except json.JSONDecodeError as jde:
            logger.error(f"Failed to decode Gemini JSON response: {jde}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="LLM returned an invalid JSON structure.",
            )
        except Exception as e:
            logger.error(f"Gemini API invocation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Gemini API error: {str(e)}",
            )

    async def _call_openai(self, prompt: str) -> Dict[str, Any]:
        api_key = settings.OPENAI_API_KEY
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="OPENAI_API_KEY is not configured in environment or .env file.",
            )

        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=api_key)
            response = await client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
            )

            raw_text = response.choices[0].message.content.strip()
            return json.loads(raw_text)

        except json.JSONDecodeError as jde:
            logger.error(f"Failed to decode OpenAI JSON response: {jde}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="LLM returned an invalid JSON structure.",
            )
        except Exception as e:
            logger.error(f"OpenAI API invocation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"OpenAI API error: {str(e)}",
            )

