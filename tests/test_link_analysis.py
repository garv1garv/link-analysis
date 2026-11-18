import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport
from app.main import app

SAMPLE_LLM_OUTPUT = {
    "brand": {
        "name": "Acme Cloud",
        "category": "Cloud Computing",
        "summary": "Enterprise cloud services and architecture."
    },
    "competitor_analysis": {
        "brand_overview": "Acme Cloud provides scalable cloud infrastructure.",
        "main_business_category": "Cloud Computing",
        "main_products_services": ["Cloud Hosting", "DevOps", "Managed Kubernetes"],
        "competitors": [
            {
                "name": "AWS",
                "main_service": "Cloud Infrastructure",
                "target_market": "Global Enterprise",
                "strengths": "Market leader, massive ecosystem",
                "gaps_weaknesses": "Complex pricing, steep learning curve"
            },
            {
                "name": "Microsoft Azure",
                "main_service": "Enterprise Cloud",
                "target_market": "Enterprises",
                "strengths": "Integration with Windows ecosystem",
                "gaps_weaknesses": "Inconsistent UI experience"
            },
            {
                "name": "Google Cloud",
                "main_service": "Data & AI Cloud",
                "target_market": "Developers & Enterprises",
                "strengths": "Superior AI and Kubernetes tooling",
                "gaps_weaknesses": "Smaller enterprise market share"
            }
        ],
        "brand_competitive_advantages": [
            "Affordable transparent pricing",
            "White-glove developer support"
        ],
        "market_positioning_opportunities": [
            "Focus on SMBs alienated by AWS pricing complexity"
        ]
    },
    "target_search_queries": [
        {
            "query": "Affordable enterprise cloud hosting",
            "platforms": ["Google", "LinkedIn"],
            "search_intent": "Service Search",
            "business_relevance": "Direct match to Acme Cloud offering",
            "target_audience": "Tech Startup CTOs"
        },
        {
            "query": "Managed Kubernetes provider",
            "platforms": ["Google", "X"],
            "search_intent": "Technical Discovery",
            "business_relevance": "High intent for container solutions",
            "target_audience": "DevOps Engineers"
        },
        {
            "query": "Best alternative to AWS for startups",
            "platforms": ["LinkedIn", "Google"],
            "search_intent": "Comparison Search",
            "business_relevance": "Addresses cost and complexity pain points",
            "target_audience": "Startup Founders"
        },
        {
            "query": "Cloud infrastructure tips",
            "platforms": ["Instagram", "Facebook"],
            "search_intent": "Educational",
            "business_relevance": "Brand awareness and thought leadership",
            "target_audience": "Junior Developers"
        },
        {
            "query": "DevOps consulting services",
            "platforms": ["LinkedIn", "Google"],
            "search_intent": "B2B Service Search",
            "business_relevance": "Drives enterprise consulting leads",
            "target_audience": "IT Directors"
        }
    ],
    "seo_improvements": {
        "primary_keyword": "Managed Cloud Hosting",
        "secondary_keywords": ["DevOps Services", "Kubernetes Management"],
        "long_tail_keywords": ["Affordable cloud hosting for startups", "Managed Kubernetes support provider"],
        "relevant_business_keywords": ["Cloud Migration", "Infrastructure as Code"],
        "recommended_title": "Acme Cloud | Reliable & Affordable Managed Cloud Hosting",
        "meta_description": "Scale your business with Acme Cloud's high-performance hosting, managed Kubernetes, and 24/7 DevOps support.",
        "supporting_content": [
            "AWS vs Acme Cloud Pricing Comparison Guide",
            "Ultimate Guide to Kubernetes for Startups"
        ]
    },
    "top_services": [
        {
            "service_name": "Managed Cloud Hosting",
            "description": "High uptime VPS and dedicated compute nodes.",
            "target_industry": "SaaS & E-commerce",
            "target_customer": "Tech Startups",
            "main_benefit": "Zero downtime and predictable monthly billing"
        },
        {
            "service_name": "Kubernetes Orchestration",
            "description": "Automated deployment and auto-scaling of container clusters.",
            "target_industry": "Enterprise Software",
            "target_customer": "DevOps Teams",
            "main_benefit": "Effortless application scaling"
        },
        {
            "service_name": "24/7 DevOps Support",
            "description": "Round-the-clock monitoring, backup, and incident response.",
            "target_industry": "Digital Businesses",
            "target_customer": "SMB IT Managers",
            "main_benefit": "Peace of mind without hiring dedicated in-house SREs"
        }
    ],
    "target_audience": {
        "primary_audience": ["Startup Founders", "CTOs"],
        "secondary_audience": ["DevOps Engineers", "System Administrators"],
        "industry_segments": ["SaaS", "FinTech", "E-commerce"],
        "business_types": ["Early-stage startups", "Growing SMBs"],
        "customer_profiles": ["Fast-moving technical founders needing reliable hosting"],
        "location_geographical_focus": "North America & Europe",
        "customer_needs_challenges": ["High cloud bills", "Complex infrastructure setup"],
        "potential_customer_interests": ["Cost optimization", "Cloud speed", "Simplicity"],
        "recommended_marketing_segments": [
            {
                "audience": "Seed to Series A Startups",
                "business_type": "Tech Companies",
                "requirement": "Predictable cloud compute with free credits"
            },
            {
                "audience": "Mid-market E-commerce",
                "business_type": "Online Retailers",
                "requirement": "High availability during seasonal traffic spikes"
            }
        ]
    }
}


@pytest.mark.asyncio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


@pytest.mark.asyncio
async def test_ssrf_rejection_in_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/link-analysis", json={"url": "http://127.0.0.1:8080"})
        assert response.status_code == 400
        assert "SSRF" in response.json()["detail"] or "internal" in response.json()["detail"]


@pytest.mark.asyncio
async def test_successful_link_analysis_flow():
    mock_scraped = {
        "title": "Acme Cloud - Enterprise Infrastructure",
        "meta_description": "Enterprise cloud services and architecture.",
        "meta_keywords": "cloud, kubernetes, hosting",
        "headings": ["H1: Enterprise Cloud"],
        "cleaned_text": "Acme Cloud provides scalable cloud hosting and devops solutions.",
        "final_url": "https://example.com"
    }

    transport = ASGITransport(app=app)
    with patch("app.services.website_extractor.WebsiteExtractor.fetch_and_extract", new=AsyncMock(return_value=mock_scraped)):
        with patch("app.services.llm_service.LLMService.analyze_website_content", new=AsyncMock(return_value=SAMPLE_LLM_OUTPUT)):
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                response = await ac.post("/link-analysis", json={"url": "https://example.com"})
                assert response.status_code == 200
                data = response.json()

                # Verify 5 sections structure
                assert data["success"] is True
                assert data["website"].rstrip("/") == "https://example.com"
                assert data["brand"]["name"] == "Acme Cloud"

                analysis = data["analysis"]
                # Section 1: Competitors
                assert len(analysis["competitor_analysis"]["competitors"]) >= 3
                assert analysis["competitor_analysis"]["competitors"][0]["name"] == "AWS"

                # Section 2: Target Search Queries (exactly 5)
                assert len(analysis["target_search_queries"]) == 5

                # Section 3: SEO Improvements
                assert "primary_keyword" in analysis["seo_improvements"]
                assert "recommended_title" in analysis["seo_improvements"]

                # Section 4: Top Services
                assert len(analysis["top_services"]) >= 3
                assert analysis["top_services"][0]["service_name"] == "Managed Cloud Hosting"

                # Section 5: Target Audience
                assert len(analysis["target_audience"]["primary_audience"]) >= 1
                assert len(analysis["target_audience"]["recommended_marketing_segments"]) >= 1
