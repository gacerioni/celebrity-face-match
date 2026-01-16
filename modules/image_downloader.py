import requests

def download_image(url: str, path: str):
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            with open(path, "wb") as f:
                f.write(resp.content)
            return True
    except:
        pass
    return False
