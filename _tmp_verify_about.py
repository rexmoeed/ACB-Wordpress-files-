import urllib.request

h = urllib.request.urlopen(
    "https://americacustomboxes.com/about-us/?nocache=formfix1", timeout=90
).read().decode("utf-8", "replace")
print("home glass css", "backdrop-filter: blur(10px)" in h)
print("quote-form id", 'id="quote-form"' in h)
print("mu css links", h.count("acb-quote-form.css"))
print("acb-about-us-css", "acb-about-us-css" in h)
