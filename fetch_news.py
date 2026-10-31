import os
import json
import urllib.request
import urllib.parse
from datetime import datetime

CLIENT_ID = os.environ.get("NAVER_CLIENT_ID")
CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET")

SEARCH_KEYWORD = "인공지능"
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
        
        existing_news = []
        if os.path.exists("news_data.json"):
            try:
                with open("news_data.json", "r", encoding="utf-8") as f:
                    existing_news = json.load(f)
            except Exception:
                existing_news = []
                
        existing_links = {item.get('link') for item in existing_news if 'link' in item}
        
        new_items = []
        for item in fetched_items:
            title = item['title'].replace('<b>', '').replace('</b>', '').replace('&quot;', '"').replace('&amp;', '&')
            description = item['description'].replace('<b>', '').replace('</b>', '').replace('&quot;', '"').replace('&amp;', '&')
            link = item.get('originallink') or item.get('link')
            pub_date = item.get('pubDate', '')
            
            if link not in existing_links:
                new_items.append({
                    "title": title,
                    "link": link,
                    "description": description,
                    "pubDate": pub_date,
                    "fetchedAt": datetime.now().strftime("%Y-%m-%d %H:%M")
                })
        
        combined_news = new_items + existing_news
        final_news = combined_news[:100]
        
        with open("news_data.json", "w", encoding="utf-8") as f:
            json.dump(final_news, f, ensure_ascii=False, indent=2)
            
        print(f"새로 추가된 뉴스: {len(new_items)}건 / 총 저장된 뉴스: {len(final_news)}건")
    else:
        print(f"API 요청 실패 응답 코드: {rescode}")
        exit(1)

except Exception as e:
    print(f"파이썬 실행 중 오류 발생: {e}")
    exit(1) # 오류 발생 시 작업을 중단하여 로그에 에러를 기록
