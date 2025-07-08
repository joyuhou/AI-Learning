cdn_domains = [
    "cdn.jsdelivr.net", "unpkg.com", "cdnjs.cloudflare.com", "ajax.googleapis.com", "stackpath.bootstrapcdn.com", "cdn.tailwindcss.com",
    "fonts.googleapis.com", "fonts.gstatic.com", "ajax.aspnetcdn.com", "use.fontawesome.com", "kit.fontawesome.com",
    "use.typekit.net", "use.typekit.com", "polyfill.io", "cdn.polyfill.io", "esm.sh", "skypack.dev",
    "vjs.zencdn.net", "cdn.plyr.io", "placekitten.com", "via.placeholder.com",
    "connect.facebook.net", "www.facebook.com", "staticxx.facebook.com", "www.googletagmanager.com", "www.googleadservices.com",
    "www.google-analytics.com", "ssl.google-analytics.com", "pagead2.googlesyndication.com", "tpc.googlesyndication.com",
    "analytics.tiktok.com", "business.tiktok.com", "ads.tiktok.com", "static.ads-twitter.com", "analytics.twitter.com",
    "snap.licdn.com", "px.ads.linkedin.com", "bat.bing.com", "ct.pinterest.com", "sc-static.net", "tr.snapchat.com",
    "cdn.taboola.com", "trc.taboola.com", "widgets.outbrain.com", "amplify.outbrain.com"
]

from urllib.parse import urlparse

def is_cdn(url_str):
    try:
        hostname = urlparse(url_str).hostname
        if not hostname:
            return False
        for cdn in cdn_domains:
            if hostname == cdn or hostname.endswith('.' + cdn):
                return True
        return False
    except Exception:
        return False 