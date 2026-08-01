#!/usr/bin/env python3
import re, urllib.request
html = urllib.request.urlopen(urllib.request.Request('https://americacustomboxes.com/',headers={'User-Agent':'Mozilla/5.0 iPhone','Cache-Control':'no-cache'}),timeout=60).read().decode('utf-8','replace')
links = re.findall(r'href="([^"]+\.css[^"]*)"', html, re.I)
print('css count', len(links))
for u in links:
    if 'elementor' in u or 'post-' in u:
        try:
            n=len(urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'A'}),timeout=20).read())
            print(n, u.split('/')[-1][:60])
        except Exception as e:
            print('FAIL', u.split('/')[-1][:40], e)
