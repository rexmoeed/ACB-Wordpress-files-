import urllib.request
h = urllib.request.urlopen("https://americacustomboxes.com/?nocache=prefaq1", timeout=90).read().decode("utf-8", "replace")
markers = [
    "acb-order-section",
    "acb-brands-choose-section",
    "acb-qf-wrap",
    "Get an Instant Quote",
    "Secure, Trusted Payment",
    "acb-faq-section",
    "Packaging Built Around",
    "Our Most Popular Custom Boxes",
]
for m in markers:
    print(m, h.find(m))
