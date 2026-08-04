<?php
/**
 * Homepage only: rich content block immediately before FAQ accordion.
 * Elementor template is not modified.
 */
add_action(
	'wp_head',
	static function () {
		if ( ! function_exists( 'is_front_page' ) || ! is_front_page() ) {
			return;
		}
		?>
<style id="acb-home-pre-faq-css">
.acb-home-pre-faq {
	width: 100%;
	max-width: 100%;
	box-sizing: border-box;
	font-family: 'Titillium Web', sans-serif;
	padding: 8px 16px 32px;
}
.acb-home-pre-faq *,
.acb-home-pre-faq *::before,
.acb-home-pre-faq *::after {
	box-sizing: border-box;
}
.acb-hpf-inner {
	max-width: 1200px;
	margin: 0 auto;
	display: flex;
	flex-direction: column;
	gap: 28px;
}
.acb-hpf-block {
	background: #000;
	border-radius: 15px;
	padding: 36px 32px;
	color: #fff;
	overflow: hidden;
}
.acb-hpf-block.acb-hpf-light {
	background: #ffffff;
	color: #374151;
	border: 1px solid #e5e7eb;
}
.acb-hpf-h2 {
	color: #ff2e2e;
	font-size: clamp(1.35rem, 4vw, 1.85rem);
	font-weight: 700;
	line-height: 1.25;
	margin: 0 0 14px;
}
.acb-hpf-block.acb-hpf-light .acb-hpf-h2 {
	color: #ff2e2e;
}
.acb-hpf-p {
	font-size: clamp(0.9375rem, 2.7vw, 1.02rem);
	line-height: 1.65;
	margin: 0 0 12px;
}
.acb-hpf-p:last-child {
	margin-bottom: 0;
}
.acb-hpf-table-wrap {
	width: 100%;
	overflow-x: auto;
	-webkit-overflow-scrolling: touch;
	margin-top: 12px;
}
.acb-hpf-table {
	width: 100%;
	min-width: 300px;
	border-collapse: collapse;
}
.acb-hpf-table th {
	background: #ff2e2e;
	color: #111827;
	font-weight: 700;
	padding: 12px 14px;
	text-align: left;
	border: 1px solid #2a2a2a;
	font-size: clamp(0.875rem, 2.5vw, 0.95rem);
}
.acb-hpf-table td {
	padding: 12px 14px;
	border: 1px solid #2a2a2a;
	vertical-align: top;
	font-size: clamp(0.875rem, 2.5vw, 0.95rem);
	line-height: 1.45;
	overflow-wrap: anywhere;
}
.acb-hpf-block.acb-hpf-light .acb-hpf-table td,
.acb-hpf-block.acb-hpf-light .acb-hpf-table th {
	border-color: #e5e7eb;
}
.acb-hpf-block:not(.acb-hpf-light) .acb-hpf-table td {
	color: #fff;
}
.acb-hpf-ul {
	margin: 8px 0 0;
	padding: 0 0 0 1.1rem;
}
.acb-hpf-ul li {
	margin: 0 0 8px;
	font-size: clamp(0.9375rem, 2.7vw, 1rem);
	line-height: 1.55;
}
.acb-hpf-ol {
	margin: 10px 0 0;
	padding: 0 0 0 1.25rem;
}
.acb-hpf-ol li {
	margin: 0 0 10px;
	font-size: clamp(0.9375rem, 2.7vw, 1rem);
	line-height: 1.55;
}
.acb-hpf-stats {
	display: grid;
	grid-template-columns: repeat(4, 1fr);
	gap: 12px;
	margin-top: 16px;
}
.acb-hpf-stat {
	text-align: center;
	padding: 16px 10px;
	border: 1px solid #2a2a2a;
	border-radius: 10px;
	background: #111111;
}
.acb-hpf-block.acb-hpf-light .acb-hpf-stat {
	background: #f9fafb;
	border-color: #e5e7eb;
}
.acb-hpf-block.acb-hpf-light .acb-hpf-stat-label {
	color: #6b7280;
}
.acb-hpf-stat-val {
	display: block;
	color: #ff2e2e;
	font-size: clamp(1.25rem, 4vw, 1.75rem);
	font-weight: 700;
	line-height: 1.2;
	margin-bottom: 6px;
}
.acb-hpf-stat-label {
	display: block;
	font-size: clamp(0.75rem, 2.3vw, 0.875rem);
	line-height: 1.35;
	color: #e5e7eb;
}
@media (max-width: 767px) {
	.acb-home-pre-faq {
		padding: 8px 12px 24px;
	}
	.acb-hpf-block {
		padding: 24px 16px;
		border-radius: 12px;
	}
	.acb-hpf-stats {
		grid-template-columns: repeat(2, 1fr);
	}
}
</style>
		<?php
	},
	106
);

add_action(
	'wp_footer',
	static function () {
		if ( ! function_exists( 'is_front_page' ) || ! is_front_page() ) {
			return;
		}
		$html = <<<'HTML'
<div class="acb-home-pre-faq" id="acb-home-pre-faq">
<div class="acb-hpf-inner">

<section class="acb-hpf-block">
<h2 class="acb-hpf-h2">Packaging Built Around Your Product</h2>
<p class="acb-hpf-p">As a custom packaging box manufacturer, we develop, produce, and deliver high-quality boxes designed around your product and your brand. Whether you sell cupcakes, candles, supplements, or subscription kits, we build packaging that protects what's inside and sells what's outside.</p>
<p class="acb-hpf-p">Every order is fully custom — your size, your material, your artwork, your finish. And because design and die setup are free, you get a premium result without the premium setup fees most suppliers tack on.</p>
</section>

<section class="acb-hpf-block">
<h2 class="acb-hpf-h2">What Makes Us the #1 Choice for Custom Packaging</h2>
<ul class="acb-hpf-ul">
<li>Free die &amp; plate setup — the setup fees other suppliers charge? We don't.</li>
<li>Free 1-color printing — get your logo on the box at no extra print cost.</li>
<li>Free professional design — our team builds your artwork and dielines for you.</li>
<li>Low minimum — just 100 boxes — order what your brand actually needs.</li>
<li>20% off your first order — a real welcome, not a gimmick.</li>
<li>Free US shipping — to all 50 states, tracked, with no hidden handling.</li>
<li>Eco-friendly materials — recyclable, biodegradable, and sustainable options.</li>
<li>24/7 support — real help by phone, email, and WhatsApp whenever you need it.</li>
</ul>
</section>

<section class="acb-hpf-block acb-hpf-light">
<h2 class="acb-hpf-h2">How Your Boxes Are Made</h2>
<p class="acb-hpf-p">Behind every clean, on-brand box is a five-stage production process built for consistency.</p>
<ol class="acb-hpf-ol">
<li><strong>Production planning</strong> — we map specs, quantities, and timelines.</li>
<li><strong>Material selection</strong> — the right board and stock for your product.</li>
<li><strong>Printing</strong> — offset, digital, or screen, matched to your run.</li>
<li><strong>Quality assurance</strong> — every order checked against your approved proof.</li>
<li><strong>Mass production</strong> — your full run, produced to the same standard.</li>
</ol>
</section>

<section class="acb-hpf-block">
<h2 class="acb-hpf-h2">Eco-Friendly Packaging, as Standard</h2>
<p class="acb-hpf-p">Sustainable packaging shouldn't be an upgrade you pay extra for. We offer biodegradable, recyclable, and sustainable materials across our catalog, so you can meet your brand's environmental goals without compromising on print quality or durability.</p>
</section>

<section class="acb-hpf-block">
<h2 class="acb-hpf-h2">America Custom Boxes at a Glance</h2>
<div class="acb-hpf-stats">
<div class="acb-hpf-stat"><span class="acb-hpf-stat-val">600+</span><span class="acb-hpf-stat-label">Packaging solutions</span></div>
<div class="acb-hpf-stat"><span class="acb-hpf-stat-val">100</span><span class="acb-hpf-stat-label">Box minimum order</span></div>
<div class="acb-hpf-stat"><span class="acb-hpf-stat-val">10–12 Days</span><span class="acb-hpf-stat-label">Standard turnaround</span></div>
<div class="acb-hpf-stat"><span class="acb-hpf-stat-val">Free</span><span class="acb-hpf-stat-label">US shipping</span></div>
</div>
</section>

</div>
</div>
HTML;
		?>
<script id="acb-home-pre-faq-inject">
(function () {
	'use strict';
	if (!document.body.classList.contains('home') || document.getElementById('acb-home-pre-faq')) {
		return;
	}
	var faq = document.querySelector('.acb-faq-section');
	if (!faq) {
		return;
	}
	var block = faq.closest('.e-con.e-parent') || faq.closest('.e-con') || faq.closest('.elementor-element');
	if (!block || !block.parentNode) {
		return;
	}
	var wrap = document.createElement('div');
	wrap.innerHTML = <?php echo wp_json_encode( trim( $html ) ); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?>;
	var root = wrap.firstElementChild;
	if (!root) {
		return;
	}
	block.parentNode.insertBefore(root, block);
})();
</script>
		<?php
	},
	106
);
