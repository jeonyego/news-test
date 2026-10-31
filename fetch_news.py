import os
import json
import urllib.request
import urllib.parse
from datetime import datetime

CLIENT_ID = os.environ.get("NAVER_CLIENT_ID", "").strip()
CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET", "").strip()

TARGET_KEYWORDS = ["국립전통예술고", "전통예술고", "전통예고", "전통예중고"]

# 부정 기사 판별용 키워드 사전 (필요시 단어 추가 가능)
NEGATIVE_WORDS = [
    "논란", "비판", "우려", "적발", "실망", "의혹", "사건", "사고", 
    "피해", "소송", "고발", "경고", "징계", "갈등", "반발", "의구심", 
    "참사", "입건", "수사", "혐의", "부실", "파문", "투서", "갑질", "성폭행", "학교폭력"
]

def analyze_sentiment(title, description):
    """제목 및 본문에서 부정 키워드 포함 여부 검사"""
    text = title + " " + description
    for word in NEGATIVE_WORDS:
        if word in text:
            return "부정"
    return "일반"

all_new_items = []

existing_news = []
if os.path.exists("news_data.json"):
    try:
        with open("news_data.json", "r", encoding="utf-8") as f:
            existing_news = json.load(f)
    except Exception:
        existing_news = []

existing_links = {item.get('link') for item in existing_news if 'link' in item}

for keyword in TARGET_KEYWORDS:
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
            
            for item in fetched_items:
                raw_title = item['title']
                raw_desc = item['description']
                
                clean_title = raw_title.replace('<b>', '').replace('</b>', '').replace('&quot;', '"').replace('&amp;', '&')
                clean_desc = raw_desc.replace('<b>', '').replace('</b>', '').replace('&quot;', '"').replace('&amp;', '&')
                link = item.get('originallink') or item.get('link')
                pub_date = item.get('pubDate', '')
                
                is_exact_match = any(target in clean_title or target in clean_desc for target in TARGET_KEYWORDS)
                
                if is_exact_match and link not in existing_links:
                    # 감성 분류 수행 (부정 vs 일반)
                    sentiment = analyze_sentiment(clean_title, clean_desc)
                    
                    all_new_items.append({
                        "keyword": keyword,
                        "title": clean_title,
                        "link": link,
                        "description": clean_desc,
                        "pubDate": pub_date,
                        "sentiment": sentiment,
                        "fetchedAt": datetime.now().strftime("%Y-%m-%d %H:%M")
                    })
                    existing_links.add(link)
    except Exception as e:
        print(f"[{keyword}] 수집 중 오류: {e}")

combined_news = all_new_items + existing_news
final_news = combined_news[:150]

with open("news_data.json", "w", encoding="utf-8") as f:
    json.dump(final_news, f, ensure_ascii=False, indent=2)

print(f"수집 완. 신규: {len(all_new_items)}건 / 총: {len(final_news)}건")
