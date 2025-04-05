from typing import List, Dict
from langchain.tools import tool
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

# import asyncio
# if hasattr(asyncio, 'WindowsProactorEventLoopPolicy'):
#     asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

@tool
def scrape_finviz_stocks(
    filter_pe: str = "low",
    start_index: int = 1,
    count: int = 20
) -> List[Dict[str, str]]:
    """
    Finviz에서 주식 데이터를 스크래핑합니다. 거래량 순으로 정렬됩니다.
    
    Args:
        filter_pe (str): P/E 비율 필터. "low"(낮은 P/E), "high"(높은 P/E), "any"(필터 없음) 중 하나
        start_index (int): 시작할 티커 인덱스 (1부터 시작, 페이지당 20개 표시)
        count (int): 가져올 티커 수 (최대 100개 권장)
    
    Returns:
        List[Dict[str, str]]: 주식 데이터 목록 (Ticker, Company, Sector, Industry, Country, Market Cap, P/E, Price, Change, Volume 포함)
    """
    # P/E 필터 매핑
    pe_filter_map = {
        "low": "fa_pe_low",
        "high": "fa_pe_high",
        "any": ""
    }
    
    # 필터 유효성 검사
    if filter_pe not in pe_filter_map:
        return [{"error": f"유효하지 않은 P/E 필터: {filter_pe}. 'low', 'high', 'any' 중 하나를 사용하세요."}]
    
    # 데이터 저장용 리스트
    all_data = []
    
    # 타임아웃 설정 (4초)
    timeout = 5000  # 밀리초 단위
    
    # 페이지 계산 (Finviz는 페이지당 20개의 결과를 보여줌)
    pages_needed = min(3, (count + 19) // 20)  # 최대 3페이지로 제한
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # ✅ 광고 & 불필요한 리소스 차단
        def intercept_request(route):
            resource_type = route.request.resource_type
            if resource_type in ["image", "stylesheet", "font", "media", "websocket", "eventsource"]:
                route.abort()
            else:
                route.continue_()
        
        page.route("**/*", intercept_request)
        
        try:
            for p_num in range(pages_needed):
                current_index = start_index + (p_num * 20)
                
                # PE 필터 적용
                pe_filter = pe_filter_map[filter_pe]
                filter_param = f"&f=exch_nasd,{pe_filter}" if pe_filter else "&f=exch_nasd"
                
                # URL 구성
                base_url = f"https://finviz.com/screener.ashx?v=111{filter_param}&o=-volume&r={current_index}"
                
                try:
                    # 페이지 로드 시작 - 4초 타임아웃 적용
                    page.goto(base_url, wait_until="domcontentloaded", timeout=timeout)
                except TimeoutError:
                    # 타임아웃 발생해도 진행
                    pass
                
                # HTML 파싱
                html_content = page.content()
                soup = BeautifulSoup(html_content, "html.parser")
                
                # 테이블 찾기 - 원본 코드와 동일한 방식
                table = soup.find("tr", id="screener-table")
                
                if table is None:
                    # 테이블이 없으면 다음 페이지로
                    continue
                
                # 원본 코드와 동일한 방식으로 데이터 추출
                rows = table.find_all("tr")[1:]
                
                for row in rows:
                    cols = row.find_all("td")
                    if len(cols) < 11:
                        continue
                    stock_data = {
                        "Ticker": cols[1].text.strip(),
                        "Company": cols[2].text.strip(),
                        "Sector": cols[3].text.strip(),
                        "Market Cap": cols[6].text.strip(),
                        "P/E": cols[7].text.strip(),
                        "Price": cols[8].text.strip(),
                        "Change": cols[9].text.strip(),
                        "Volume": cols[10].text.strip()
                    }
                    all_data.append(stock_data)
                    
                    # 요청한 개수에 도달하면 중단
                    if len(all_data) >= count:
                        break
                
                # 요청한 개수에 도달하면 다음 페이지 호출 중단
                if len(all_data) >= count:
                    break
        
        except TimeoutError:
            # 타임아웃 오류는 무시하고 수집된 데이터 반환
            pass
        except Exception as e:
            # 다른 오류 발생 시 부분적으로라도 데이터 반환
            if not all_data:
                return [{"error": f"데이터 로드 중 오류 발생: {str(e)}"}]
        finally:
            browser.close()
    
    # 결과가 없으면 오류 메시지 반환
    if not all_data:
        return [{"error": "데이터를 찾을 수 없습니다. 타임아웃이 너무 짧거나 페이지 구조가 변경되었을 수 있습니다."}]
    
    # 헤더 생성
    headers = list(all_data[0].keys())
    markdown_table = "| " + " | ".join(headers) + " |\n"
    markdown_table += "| " + " | ".join(["---"] * len(headers)) + " |\n"
    
    # 데이터 행 추가
    for item in all_data:
        markdown_table += "| " + " | ".join(str(item[header]) for header in headers) + " |\n"
    
    return markdown_table