#!/usr/bin/env python3
import base64, json, urllib.request
LIVE = "https://americacustomboxes.com"
auth = {"Authorization": "Basic "+base64.b64encode(b"admin:XFxg 7dCD 7FE9 7K3z W6mN 5FIh").decode(), "Content-Type": "application/json"}
CODE = r"""add_action('init', static function () {
	if ( get_option('acb_header106_css_v2') ) return;
	if ( ! class_exists('\Elementor\Plugin') ) return;
	try { \Elementor\Core\Files\CSS\Post::create(106)->update(); } catch (\Throwable $e) {}
	\Elementor\Plugin::$instance->files_manager->clear_cache();
	update_option('acb_header106_css_v2', 1);
}, 5);"""
snips = json.loads(urllib.request.urlopen(urllib.request.Request(LIVE+"/wp-json/code-snippets/v1/snippets?per_page=100",headers=auth),timeout=60).read())
ex = next((s for s in snips if s.get("name")=="ACB Header106 CSS bump"), None)
payload = {"name":"ACB Header106 CSS bump","code":CODE,"scope":"global","active":True,"priority":3,"desc":"one-time"}
if ex:
    urllib.request.urlopen(urllib.request.Request(LIVE+f"/wp-json/code-snippets/v1/snippets/{ex['id']}",data=json.dumps(payload).encode(),headers=auth,method="PUT"),timeout=60)
else:
    urllib.request.urlopen(urllib.request.Request(LIVE+"/wp-json/code-snippets/v1/snippets",data=json.dumps(payload).encode(),headers=auth,method="POST"),timeout=60)
for u in [LIVE+"/", LIVE+"/?nocache=1"]:
    urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"A","Cache-Control":"no-cache"}),timeout=60)
html = urllib.request.urlopen(urllib.request.Request(LIVE+"/?t=2",headers={"User-Agent":"Mozilla/5.0","Cache-Control":"no-cache"}),timeout=60).read().decode()
print("Fixly in html:", "Fixly" in html)
print("ACB in nav logo:", "elementskit-nav-logo" in html and "Acb-logo" in html)
