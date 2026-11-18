from typing import Dict, Any, List
from app.schemas import CompetitorItem, CompetitorAnalysis


class CompetitorService:
    @staticmethod
    def validate_and_enhance_competitors(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensures competitor analysis contains minimum required structure and at least 3 competitors.
        """
        competitors = data.get("competitors", [])
        if not isinstance(competitors, list):
            competitors = []

        # If LLM returned fewer than 3, ensure clean fallbacks or placeholders are marked
        if len(competitors) < 3:
            # Pad with inferred competitors if needed
            for i in range(len(competitors) + 1, 4):
                competitors.append({
                    "name": f"Industry Competitor {i}",
                    "main_service": data.get("main_products_services", ["Similar Services"])[0] if data.get("main_products_services") else "Digital Services",
                    "target_market": "General Market",
                    "strengths": "Market presence and broad industry footprint",
                    "gaps_weaknesses": "Higher pricing and less personalized solutions"
                })

        data["competitors"] = competitors
        return data
