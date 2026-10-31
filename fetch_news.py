import os
import json
import urllib.request
import urllib.parse
from datetime import datetime

# 1. 환경변수에서 네이버 API 키 가져오기
CLIENT_ID = os.environ.get("NAVER_CLIENT_ID")
CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET")

# 2. 검색 설정 (원하는 검색 키워드 지정)
SEARCH_KEYWORD = "인공지능"  # <--- 원하는 키워드로 변경 가능
encText = urllib.parse.quote(SEARCH_KEYWORD)
url = f"https://openapi.naver.com/v1/search/news.json?query={encText}&display=20&sort=date"

request = urllib.request.Request(url)
request.add_header("X-Naver-Client-Id", CLIENT_ID)
request.add_header("X-Naver-Client-Secret", CLIENT_SECRET)

try:
    response = urllib.request.urlopen(request)
    rescode = response.getcode()
    
    if rescode == 200:
        response_body = response.read()
        data = json.loads(response_body.decode('utf-8'))
        fetched_items = data.get('items', [])
        
        # 기존 저장된 데이터 불러오기 (중복 방지용)
        existing_news = []
        if os.path.exists("news_data.json"):
            try:
                with open("news_data.json", "r", encoding="utf-8") as f:
                    existing_news = json.load(f)
            except Exception:
                existing_news = []
                
        existing_links = {item['link'] for item in existing_news}
        
        new_items = []
        for item in fetched_items:
            # HTML 태그 제거 및 데이터 정리
            title = item['title'].replace('<b>', '').replace('</b>', '').replace('&quot;', '"').replace('&amp;', '&')
            description = item['description'].replace('<b>', '').replace('</b>', '').replace('&quot;', '"').replace('&amp;', '&')
            link = item['originallink'] if item['originallink'] else item['link']
            pub_date = item['pubDate']
            
            if link not in existing_links:
                new_items.append({
                    "title": title,
                    "link": link,
                    "description": description,
                    "pubDate": pub_date,
                    "fetchedAt": datetime.now().strftime("%Y-%m-%d %H:%M")
                })
        
        # 최신 뉴스를 맨 위에 추가하고 최대 100개까지만 유지
        combined_news = new_items + existing_news
        final_news = combined_news[:100]
        
        with open("news_data.json", "w", encoding="utf-8") as f:
            json.dump(final_news, f, ensure_ascii=False, indent=2)
            
        print(f"새로 추가된 뉴스: {len(new_items)}건 / 총 저장된 뉴스: {len(final_news)}건")
    else:
        print("API 요청 실패 Error Code:", rescode)

except Exception as e:
    print("오류 발생:", e)
