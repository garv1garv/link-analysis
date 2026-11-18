from typing import Dict, Any
from app.schemas import (
    LinkAnalysisResponse,
    BrandSummary,
    FullAnalysis,
    CompetitorAnalysis,
    TargetSearchQuery,
    SEOImprovements,
    ServiceItem,
    TargetAudience,
)
from app.services.website_extractor import WebsiteExtractor
from app.services.llm_service import LLMService
from app.services.competitor_service import CompetitorService


class AnalysisService:
    def __init__(self):
        self.extractor = WebsiteExtractor()
        self.llm_service = LLMService()

    async def analyze_url(self, url: str) -> LinkAnalysisResponse:
        """
        Coordinates full analysis pipeline:
        1. Fetch and clean website HTML
        2. Call LLM for 5-section intelligence
        3. Parse, structure, and validate into Pydantic models
        """
        # Step 1: Web scraping
        extracted_data = await self.extractor.fetch_and_extract(url)

        # Step 2: LLM analysis
        raw_result = await self.llm_service.analyze_website_content(extracted_data, url)

        # Step 3: Validate and normalize components
        brand_raw = raw_result.get("brand", {})
        brand = BrandSummary(
            name=brand_raw.get("name", extracted_data.get("title") or "Unknown Brand"),
            category=brand_raw.get("category", "General Business"),
            summary=brand_raw.get("summary", extracted_data.get("meta_description") or "Business overview"),
        )

        # Section 1: Competitors
        comp_raw = raw_result.get("competitor_analysis", {})
        comp_raw = CompetitorService.validate_and_enhance_competitors(comp_raw)
        competitor_analysis = CompetitorAnalysis(
            brand_overview=comp_raw.get("brand_overview", brand.summary),
            main_business_category=comp_raw.get("main_business_category", brand.category),
            main_products_services=comp_raw.get("main_products_services", []),
            competitors=comp_raw.get("competitors", []),
            brand_competitive_advantages=comp_raw.get("brand_competitive_advantages", []),
            market_positioning_opportunities=comp_raw.get("market_positioning_opportunities", []),
        )

        # Section 2: Search Queries (exactly 5)
        queries_raw = raw_result.get("target_search_queries", [])
        if not isinstance(queries_raw, list):
            queries_raw = []

        default_platforms = [
            ["Google", "LinkedIn"],
            ["Facebook", "Instagram"],
            ["Google", "X"],
            ["LinkedIn", "Google"],
            ["Instagram", "Facebook"]
        ]
        
        target_queries = []
        for i, q in enumerate(queries_raw[:5]):
            if isinstance(q, dict):
                target_queries.append(TargetSearchQuery(
                    query=q.get("query", f"Top {brand.category} solutions"),
                    platforms=q.get("platforms", default_platforms[i % len(default_platforms)]),
                    search_intent=q.get("search_intent", "Service Search"),
                    business_relevance=q.get("business_relevance", f"High relevance to {brand.name}"),
                    target_audience=q.get("target_audience", "Potential Customers"),
                ))

        # Ensure exactly 5 queries
        while len(target_queries) < 5:
            idx = len(target_queries)
            target_queries.append(TargetSearchQuery(
                query=f"{brand.name} {brand.category} services",
                platforms=default_platforms[idx % len(default_platforms)],
                search_intent="Discovery",
                business_relevance=f"Relevant to {brand.category} discovery",
                target_audience="Target Market",
            ))

        # Section 3: SEO Improvements
        seo_raw = raw_result.get("seo_improvements", {})
        seo_improvements = SEOImprovements(
            primary_keyword=seo_raw.get("primary_keyword", brand.category),
            secondary_keywords=seo_raw.get("secondary_keywords", []),
            long_tail_keywords=seo_raw.get("long_tail_keywords", []),
            relevant_business_keywords=seo_raw.get("relevant_business_keywords", []),
            recommended_title=seo_raw.get("recommended_title", f"{brand.name} | Expert {brand.category}"),
            meta_description=seo_raw.get("meta_description", brand.summary),
            supporting_content=seo_raw.get("supporting_content", []),
        )

        # Section 4: Top Services (3 to 5)
        services_raw = raw_result.get("top_services", [])
        top_services = []
        for s in (services_raw if isinstance(services_raw, list) else [])[:5]:
            if isinstance(s, dict):
                top_services.append(ServiceItem(
                    service_name=s.get("service_name", "Core Service"),
                    description=s.get("description", "Comprehensive service offering"),
                    target_industry=s.get("target_industry", brand.category),
                    target_customer=s.get("target_customer", "Enterprises & SMBs"),
                    main_benefit=s.get("main_benefit", "Delivers scalable value and efficiency"),
                ))

        while len(top_services) < 3:
            top_services.append(ServiceItem(
                service_name=f"{brand.category} Consulting & Execution",
                description=f"Tailored {brand.category} services designed for modern businesses.",
                target_industry=brand.category,
                target_customer="Businesses seeking growth",
                main_benefit="Boosts efficiency and competitive positioning",
            ))

        # Section 5: Target Audience
        aud_raw = raw_result.get("target_audience", {})
        target_audience = TargetAudience(
            primary_audience=aud_raw.get("primary_audience", ["Industry Decision Makers"]),
            secondary_audience=aud_raw.get("secondary_audience", ["Individual consumers & SMBs"]),
            industry_segments=aud_raw.get("industry_segments", [brand.category]),
            business_types=aud_raw.get("business_types", ["Startups", "Enterprises", "SMBs"]),
            customer_profiles=aud_raw.get("customer_profiles", ["High-intent buyers looking for reliable solutions"]),
            location_geographical_focus=aud_raw.get("location_geographical_focus", "Global / Flexible"),
            customer_needs_challenges=aud_raw.get("customer_needs_challenges", ["Cost, efficiency, and scaling"]),
            potential_customer_interests=aud_raw.get("potential_customer_interests", ["Quality, support, and speed"]),
            recommended_marketing_segments=aud_raw.get("recommended_marketing_segments", [
                {"audience": "Segment 1", "business_type": "SMBs", "requirement": "Cost-effective solutions"},
                {"audience": "Segment 2", "business_type": "Enterprises", "requirement": "Scalable robust infrastructure"}
            ]),
        )

        full_analysis = FullAnalysis(
            competitor_analysis=competitor_analysis,
            target_search_queries=target_queries,
            seo_improvements=seo_improvements,
            top_services=top_services,
            target_audience=target_audience,
        )

        return LinkAnalysisResponse(
            success=True,
            website=url,
            brand=brand,
            analysis=full_analysis,
        )
