import sys
sys.path.insert(0, 'app')
import asyncio
from app.services.ai_service import AIService

async def test_ai():
    service = AIService()
    try:
        result = await service.analyze_operational_risk(
            unanswered_count=5,
            unanswered_threshold=3,
            no_show_rate=0.2,
            no_show_threshold=0.15,
            pending_forms=2,
            pending_forms_threshold=3,
            low_stock_items=[],
            booking_trends={}
        )
        print('AI Service Result:')
        print(f'  OK: {result.get("ok", False)}')
        print(f'  Risk Level: {result.get("overall_risk_level", "unknown")}')
        print(f'  Summary: {result.get("summary", "no summary")}')
        if not result.get('ok', False):
            print(f'  Error: {result.get("error", "unknown error")}')
    except Exception as e:
        print(f'Exception: {e}')

if __name__ == '__main__':
    asyncio.run(test_ai())
