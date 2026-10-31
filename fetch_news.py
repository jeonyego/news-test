import os
import json
import urllib.request
import urllib.parse
from datetime import datetime

# GitHub Secrets에서 인증 키 가져오기
CLIENT_ID = os.environ.get("NAVER_CLIENT_ID", "").strip()
CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET", "").strip()

# 지정 키워드 (정확히 일치하는 단어만 필터링)
TARGET_KEYWORDS = ["국립전통예술고", "전통예술고", "전통예고", "전통예중고"]

all_new_items = []

# 기존 데이터 불러오기
existing_news = []
if os.path.exists("news_data.json"):
    try:
        with open("news_data.json", "r", encoding="utf-8") as f:
            existing_news = json.load(f)
    except Exception:
        existing_news = []

# 중복 방지를 위한 기저장 고유 링크 세트
existing_links = {item.get('link') for item in existing_news if 'link' in item}

for keyword in TARGET_KEYWORDS:
    # 정확한 문구 검색을 위해 따옴표 포함 인코딩
    encText = urllib.parse.quote(f'"{keyword}"')
    url = f"https://naverapihub.apigw.ntruss.com/search/v1/news?query={encText}&display=20&sort=date"
    
    request = urllib.request.Request(url)
    request.add_header("X-NCP-APIGW-API-KEY-ID", CLIENT_ID)
    request.add_header("X-NCP-APIGW-API-KEY", CLIENT_SECRET)
    
    try:
        response = urllib.request.urlopen(request)
        if response.getcode() == 200:
            data = json.loads(response.read().decode('utf-8'))
            fetched_items = data.get('items', [])
            
            count = 0
            for item in fetched_items:
                raw_title = item['title']
                raw_desc = item['description']
                
                # HTML 태그 제거 및 특수문자 변환
                clean_title = raw_title.replace('<b>', '').replace('</b>', '').replace('&quot;', '"').replace('&amp;', '&')
                clean_desc = raw_desc.replace('<b>', '').replace('</b>', '').replace('&quot;', '"').replace('&amp;', '&')
                link = item.get('originallink') or item.get('link')
                pub_date = item.get('pubDate', '')
                
                # [핵심 필터링] 제목이나 본문에 지정한 키워드가 '정확히' 포함되어 있는지 검증
                is_exact_match = any(target in clean_title or target in clean_desc for target in TARGET_KEYWORDS)
                
                if is_exact_match and link not in existing_links:
                    all_new_items.append({
                        "keyword": keyword,
                        "title": clean_title,
                        "link": link,
                        "description": clean_desc,
                        "pubDate": pub_date,
                        "fetchedAt": datetime.now().strftime("%Y-%m-%d %H:%M")
                    })
                    existing_links.add(link)
                    count += 1
                    
            print(f"[{keyword}] 탐색 완료 (정확히 일치하는 신규 뉴스: {count}건)")
        else:
            print(f"[{keyword}] 요청 실패 (응답 코드: {response.getcode()})")
    except Exception as e:
        print(f"[{keyword}] 수집 중 오류: {e}")

# 신규 뉴스 + 기존 뉴스 합치기 (최대 150건 유지)
combined_news = all_new_items + existing_news
final_news = combined_news[:150]

with open("news_data.json", "w", encoding="utf-8") as f:
    json.dump(final_news, f, ensure_ascii=False, indent=2)

print(f"최종 완료! 추가된 뉴스: {len(all_new_items)}건 / 총 저장된 뉴스: {len(final_news)}건")
