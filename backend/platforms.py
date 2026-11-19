import os, re, requests
from urllib.parse import urlparse, parse_qs

def identify_platform(url):
    host = (urlparse(url).hostname or "").lower().replace("www.","")
    if host in ("youtube.com","youtu.be","m.youtube.com"): return "youtube"
    if host in ("instagram.com",): return "instagram"
    if host in ("facebook.com","fb.watch","m.facebook.com"): return "facebook"
    if host in ("x.com","twitter.com"): return "x"
    if host in ("reddit.com","www.reddit.com","redd.it"): return "reddit"
    raise ValueError("Unsupported social media domain. Supported: YouTube, Instagram, Facebook, X and Reddit.")

def youtube_video_id(url):
    p=urlparse(url)
    if p.hostname and "youtu.be" in p.hostname: return p.path.strip("/").split("/")[0]
    if p.path == "/watch": return parse_qs(p.query).get("v",[None])[0]
    m=re.search(r"/(?:embed|shorts|live)/([^/?]+)",p.path)
    return m.group(1) if m else None

def fetch_youtube(url):
    key=os.getenv("YOUTUBE_API_KEY")
    if not key: raise RuntimeError("YouTube API key is not configured. Add YOUTUBE_API_KEY to backend/.env.")
    vid=youtube_video_id(url)
    if not vid: raise ValueError("Could not identify a YouTube video ID.")
    base="https://www.googleapis.com/youtube/v3/"
    r=requests.get(base+"videos",params={"part":"snippet,statistics","id":vid,"key":key},timeout=20)
    r.raise_for_status()
    items=r.json().get("items",[])
    if not items: raise ValueError("Video not found or not accessible.")
    snippet=items[0]["snippet"]
    comments=[]
    token=None
    for _ in range(5):
        params={"part":"snippet","videoId":vid,"maxResults":100,"textFormat":"plainText","key":key}
        if token: params["pageToken"]=token
        cr=requests.get(base+"commentThreads",params=params,timeout=20)
        if cr.status_code == 403:
            raise RuntimeError("YouTube comments are disabled or API quota/permissions prevent access.")
        cr.raise_for_status()
        data=cr.json()
        comments += [x["snippet"]["topLevelComment"]["snippet"]["textDisplay"] for x in data.get("items",[])]
        token=data.get("nextPageToken")
        if not token: break
    return {"platform":"youtube","title":snippet.get("title",""),"description":snippet.get("description",""),
            "embed_url":f"https://www.youtube-nocookie.com/embed/{vid}","comments":comments}

def fetch_social(url):
    platform=identify_platform(url)
    if platform=="youtube": return fetch_youtube(url)
    messages={
      "instagram":"Instagram access requires an eligible Meta app, account permissions and supported Graph API media access. Configure an authorized integration before using this URL.",
      "facebook":"Facebook content access requires an eligible Meta app and the appropriate permissions for the Page/content.",
      "x":"X content access requires an approved X developer project and API credentials with suitable read access.",
      "reddit":"Reddit access requires an application registered with Reddit and compliant API credentials/rate limits."
    }
    raise RuntimeError(messages[platform])
