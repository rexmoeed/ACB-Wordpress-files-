<?php
/**
 * Homepage only: "Our Most Popular Custom Boxes" table after Why Brands Choose, before quote form.
 */
add_action(
	'wp_head',
	static function () {
		if ( ! function_exists( 'is_front_page' ) || ! is_front_page() ) {
			return;
		}
		?>
<style id="acb-popular-boxes-css">
.acb-popular-boxes-section {
	width: 100%;
	max-width: 100%;
	box-sizing: border-box;
	font-family: 'Titillium Web', sans-serif;
	padding: 0 16px 36px;
	margin: 0 auto;
}
.acb-popular-boxes-section *,
.acb-popular-boxes-section *::before,
.acb-popular-boxes-section *::after {
	box-sizing: border-box;
}
.acb-popular-boxes-inner {
	max-width: 1200px;
	margin: 0 auto;
	background: #000000;
	color: #ffffff;
	border: none;
	border-radius: 15px;
	padding: 36px 32px 40px;
	overflow: hidden;
}
.acb-popular-boxes-heading {
	color: #ff2e2e;
	font-size: clamp(1.35rem, 4vw, 1.85rem);
	font-weight: 700;
	line-height: 1.25;
	margin: 0 0 14px;
}
.acb-popular-boxes-intro {
	font-size: clamp(0.9375rem, 2.7vw, 1.02rem);
	line-height: 1.65;
	margin: 0 0 12px;
	color: #ffffff;
}
.acb-popular-boxes-table-wrap {
	width: 100%;
	overflow-x: auto;
	-webkit-overflow-scrolling: touch;
	margin-top: 8px;
}
.acb-popular-boxes-table {
	width: 100%;
	min-width: 300px;
	border-collapse: collapse;
}
.acb-popular-boxes-table thead th {
	background: #ff2e2e;
	color: #ffffff;
	font-weight: 700;
	padding: 12px 14px;
	text-align: left;
	border: 1px solid #2a2a2a;
	font-size: clamp(0.875rem, 2.5vw, 0.95rem);
}
.acb-popular-boxes-table tbody td {
	padding: 12px 14px;
	border: 1px solid #2a2a2a;
	vertical-align: top;
	font-size: clamp(0.875rem, 2.5vw, 0.95rem);
	line-height: 1.45;
	color: #ffffff;
	overflow-wrap: anywhere;
	background: transparent;
}
.acb-popular-boxes-table tbody tr:nth-child(even) {
	background: #111111;
}
.acb-popular-boxes-table tbody tr:nth-child(odd) {
	background: #000000;
}
@media (max-width: 600px) {
	.acb-popular-boxes-inner {
		padding: 24px 16px 28px;
	}
	.acb-popular-boxes-table thead th,
	.acb-popular-boxes-table tbody td {
		padding: 10px 10px;
	}
}
</style>
		<?php
	},
	105
);

add_action(
	'wp_footer',
	static function () {
		if ( ! function_exists( 'is_front_page' ) || ! is_front_page() ) {
			return;
		}
		?>
<script id="acb-popular-boxes-inject">
(function () {
	'use strict';
	if (!document.body.classList.contains('home') || document.getElementById('acb-popular-boxes-section')) {
		return;
	}
	var brands = document.getElementById('acb-brands-choose-section');
	if (!brands) {
		return;
	}
	var html = <?php echo wp_json_encode( <<<'HTML'
<section class="acb-popular-boxes-section" id="acb-popular-boxes-section" aria-labelledby="acb-popular-boxes-heading">
<div class="acb-popular-boxes-inner">
<h2 class="acb-popular-boxes-heading" id="acb-popular-boxes-heading">Our Most Popular Custom Boxes</h2>
<p class="acb-popular-boxes-intro">Explore 600+ packaging styles across food, retail, beauty, cannabis, and e-commerce. A few of our best-sellers:</p>
<div class="acb-popular-boxes-table-wrap">
<table class="acb-popular-boxes-table">
<thead><tr><th scope="col">Product</th><th scope="col">Best For</th></tr></thead>
<tbody>
<tr><td>Bakery Boxes</td><td>Cupcakes, cookies, cakes &amp; pastries — food-safe board</td></tr>
<tr><td>CBD Boxes</td><td>Compliant, retail-ready cannabis &amp; CBD packaging</td></tr>
<tr><td>Mailer Boxes</td><td>E-commerce shipping &amp; unboxing experiences</td></tr>
<tr><td>Kraft Boxes</td><td>Eco-friendly, recyclable everyday packaging</td></tr>
<tr><td>Rigid Boxes</td><td>Luxury, high-perceived-value products</td></tr>
<tr><td>Candle Boxes</td><td>Candles, gifts &amp; home fragrance brands</td></tr>
<tr><td>Display Boxes</td><td>Retail counter &amp; point-of-purchase display</td></tr>
<tr><td>Stand-Up Pouches &amp; Mylar Bags</td><td>Snacks, coffee, pet treats &amp; more</td></tr>
</tbody>
</table>
</div>
</div>
</section>
HTML
		); ?>;
	var wrap = document.createElement('div');
	wrap.innerHTML = html.trim();
	var section = wrap.firstElementChild;
	if (!section || !brands.parentNode) {
		return;
	}
	brands.parentNode.insertBefore(section, brands.nextSibling);
})();
</script>
		<?php
	},
	106
);
