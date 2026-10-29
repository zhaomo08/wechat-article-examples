"""只处理已明确配置的公开文章样例，不请求网络，不展开短链接。"""
from urllib.parse import unquote_plus, urlsplit

DROP = {"utm_source", "utm_medium", "utm_campaign"}
SENSITIVE = {"signature", "sig", "token", "access_token", "x-amz-signature", "x-goog-signature"}


def clean_article_url(raw, host="example.com"):
    try:
        parsed = urlsplit(raw)
    except ValueError:
        return raw
    if parsed.scheme not in {"http", "https"} or parsed.hostname != host:
        return raw
    if not parsed.path.startswith("/articles/") or parsed.username or parsed.password:
        return raw
    main, fragment_sep, fragment = raw.partition("#")
    base, query_sep, query = main.partition("?")
    if not query_sep:
        return raw
    pairs = query.split("&")
    keys = [unquote_plus(pair.partition("=")[0]) for pair in pairs]
    if any(key.lower() in SENSITIVE for key in keys):
        return raw
    kept = [pair for pair, key in zip(pairs, keys) if key not in DROP]
    if len(kept) == len(pairs):
        return raw
    return base + ("?" + "&".join(kept) if kept else "") + fragment_sep + fragment


if __name__ == "__main__":
    cases = [
        ("article", "https://example.com/articles/demo?page=2&utm_source=chat#part"),
        ("encoding", "https://example.com/articles/demo?q=a%20b&tag=one&tag=two&empty=&utm_medium=social"),
        ("unknown", "https://example.com/articles/demo?a=UNKNOWN&utm_campaign=sample"),
        ("signed", "https://example.com/articles/demo?token=FAKE&utm_source=chat"),
        ("other_host", "https://x.com/example/status/123?a=UNKNOWN"),
    ]
    for name, url in cases:
        print(name + ": " + clean_article_url(url))
