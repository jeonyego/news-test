import os
import json
import urllib.request
import urllib.parse
from datetime import datetime

# GitHub Secrets에서 인증 키 불러오기
CLIENT_ID = os.environ.get("NAVER_CLIENT_ID", "").strip()
CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET", "").strip()

# 수집할 다중 키워드 리스트 (원하는 키워드를 자유롭게 추가/수정 가능)
KEYWORDS = ["전통예술고", "전통예고", "전통예술중고", "국립전통예고", "왕기철"]

all_new_items = []

# 기존 데이터 불러오기
existing_news = []
if os.path.exists("news_data.json"):
    try:
        with open("news_data.json", "r", encoding="utf-8") as f:
            existing_news = json.load(f)
    except Exception:
        existing_news = []

# 중복 방지를 위한 기존 링크 세트 (link + keyword 조합으로 식별)
existing_identifiers = {f"{item.get('keyword')}_{item.get('link')}" for item in existing_news if 'link' in item}

# 키워드별 순회 수집
for keyword in KEYWORDS:
    encText = urllib.parse.quote(keyword)
    url = f"https://naverapihub.apigw.ntruss.com/search/v1/news?query={encText}&display=15&sort=date"
    
    request = urllib.request.Request(url)
    request.add_header("X-NCP-APIGW-API-KEY-ID", CLIENT_ID)
    request.add_header("X-NCP-APIGW-API-KEY", CLIENT_SECRET)
    
    try:
        response = urllib.request.urlopen(request)
        if response.getcode() == 200:
            data = json.loads(response.read().decode('utf-8'))
            fetched_items = data.get('items', [])
            
            for item in fetched_items:
                title = item['title'].replace('<b>', '').replace('</b>', '').replace('&quot;', '"').replace('&amp;', '&')
                description = item['description'].replace('<b>', '').replace('</b>', '').replace('&quot;', '"').replace('&amp;', '&')
                link = item.get('originallink') or item.get('link')
                pub_date = item.get('pubDate', '')
                
                identifier = f"{keyword}_{link}"
                if identifier not in existing_identifiers:
                    all_new_items.append({
                        "keyword": keyword,
                        "title": title,
                        "link": link,
                        "description": description,
                        "pubDate": pub_date,
                        "fetchedAt": datetime.now().strftime("%Y-%m-%d %H:%M")
                    })
                    existing_identifiers.add(identifier)
                    
            print(f"[{keyword}] 수집 완료")
        else:
            print(f"[{keyword}] 요청 실패 (응답 코드: {response.getcode()})")
    except Exception as e:
        print(f"[{keyword}] 수집 중 에러 발생: {e}")

# 신규 데이터와 기존 데이터 합치기 (최대 150건 유지)
combined_news = all_new_items + existing_news
final_news = combined_news[:150]

with open("news_data.json", "w", encoding="utf-8") as f:
    json.dump(final_news, f, ensure_ascii=False, indent=2)

print(f"전체 수집 완료! 새로 추가된 뉴스: {len(all_new_items)}건 / 총 저장된 뉴스: {len(final_news)}건")
