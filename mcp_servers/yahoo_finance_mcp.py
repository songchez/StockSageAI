import yfinance as yf
from mcp.server.fastmcp import FastMCP
import traceback
from typing import Dict, Any

# FastMCP 서버 초기화
mcp = FastMCP("YahooFinance")

@mcp.tool()
def get_stock_data(symbol: str) -> Dict[str, Any]:
    """현재 주식 데이터를 가져옵니다.
    
    Args:
        symbol (str): 주식 티커 심볼 (예: AAPL)
    
    Returns:
        Dict[str, Any]: 주식 데이터
    """
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        
        return {
            "symbol": symbol,
            "name": info.get("shortName", ""),
            "current_price": info.get("currentPrice", 0),
            "previous_close": info.get("previousClose", 0),
            "market_cap": info.get("marketCap", 0),
            "pe_ratio": info.get("trailingPE", 0),
            "dividend_yield": info.get("dividendYield", 0) * 100 if info.get("dividendYield") else 0,
        }
        
    except Exception as e:
        return {
            "error": str(e), 
            "symbol": symbol, 
            "traceback": traceback.format_exc()
        }

@mcp.tool()
def get_historical_prices(symbol: str, period: str = "6mo") -> Dict[str, Any]:
    """과거 주가 데이터를 가져옵니다.
    
    Args:
        symbol (str): 주식 티커 심볼
        period (str, optional): 데이터 기간. 기본값은 "6mo".
    
    Returns:
        Dict[str, Any]: 과거 주가 데이터
    """
    try:
        stock = yf.Ticker(symbol)
        history = stock.history(period=period)
        
        # DataFrame을 기본 딕셔너리 형태로 변환
        historical_prices = history[['Close']].reset_index().to_dict(orient='records')
        
        return {
            "symbol": symbol,
            "period": period,
            "prices": historical_prices
        }
        
    except Exception as e:
        return {
            "error": str(e), 
            "symbol": symbol, 
            "traceback": traceback.format_exc()
        }

@mcp.tool()
def get_company_info(symbol: str) -> Dict[str, Any]:
    """회사 기본 정보를 가져옵니다.
    
    Args:
        symbol (str): 주식 티커 심볼
    
    Returns:
        Dict[str, Any]: 회사 정보
    """
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        
        return {
            "symbol": symbol,
            "name": info.get("longName", ""),
            "sector": info.get("sector", ""),
            "industry": info.get("industry", ""),
            "description": info.get("longBusinessSummary", "")
        }
        
    except Exception as e:
        return {
            "error": str(e), 
            "symbol": symbol, 
            "traceback": traceback.format_exc()
        }

@mcp.tool()
def get_recommendations(symbol: str) -> Dict[str, Any]:
    """애널리스트 추천을 가져옵니다.
    
    Args:
        symbol (str): 주식 티커 심볼
    
    Returns:
        Dict[str, Any]: 애널리스트 추천 정보
    """
    try:
        stock = yf.Ticker(symbol)
        recommendations = stock.recommendations
        
        return {
            "symbol": symbol,
            "recommendations": recommendations.to_dict(orient='records') if not recommendations.empty else []
        }
        
    except Exception as e:
        return {
            "error": str(e), 
            "symbol": symbol, 
            "traceback": traceback.format_exc()
        }

if __name__ == "__main__":
    print("Yahoo Finance MCP 서버 시작 중...")
    mcp.run(transport='stdio')