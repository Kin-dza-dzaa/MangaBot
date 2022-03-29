import requests


HEADERS = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36'
}


# Тут парситься JSON косяк может быть в 17 строке!!!
def check(chapter_id):
    newest_chapter = float(0)
    url_chapter = f"https://api.mangadex.org/manga/{chapter_id}/aggregate"
    url_name = f"https://api.mangadex.org/manga/{chapter_id}"
    request_chapter = requests.get(url_chapter, headers=HEADERS).json()
    for i in request_chapter['volumes']:
        for j in request_chapter['volumes'][i]['chapters']:
            if type(j) is str:
                if newest_chapter < float(j):
                    newest_chapter = float(j)
    request_name = requests.get(url_name, headers=HEADERS).json()
    title_name = request_name['data']['attributes']['title']['en']
    return newest_chapter, title_name
