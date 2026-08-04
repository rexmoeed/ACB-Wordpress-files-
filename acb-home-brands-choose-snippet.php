<?php
/**
 * Homepage only: "Why Brands Choose" table after order process, before quote form.
 */
add_action(
	'wp_head',
	static function () {
		if ( ! function_exists( 'is_front_page' ) || ! is_front_page() ) {
			return;
		}
		?>
<style id="acb-brands-choose-css">
.acb-brands-choose-section {
	width: 100%;
	max-width: 100%;
	box-sizing: border-box;
	font-family: 'Titillium Web', sans-serif;
	padding: 0 16px 40px;
	margin: 0 auto;
}
.acb-brands-choose-section *,
.acb-brands-choose-section *::before,
.acb-brands-choose-section *::after {
	box-sizing: border-box;
}
.acb-brands-choose-inner {
	max-width: 1200px;
	margin: 0 auto;
	background: #000000;
	border-radius: 15px;
	padding: 40px 36px 44px;
	overflow: hidden;
}
.acb-brands-choose-heading {
	color: #FF2E2E;
	font-size: clamp(1.5rem, 4.5vw, 2rem);
	font-weight: 700;
	line-height: 1.2;
	margin: 0 0 12px;
	letter-spacing: -0.02em;
}
.acb-brands-choose-rule {
	border: 0;
	border-top: 1px solid rgba(255, 255, 255, 0.15);
	margin: 0 0 16px;
}
.acb-brands-choose-intro {
	color: #ffffff;
	font-size: clamp(0.9375rem, 2.8vw, 1.05rem);
	line-height: 1.6;
	margin: 0 0 24px;
	max-width: 920px;
}
.acb-brands-table-wrap {
	width: 100%;
	max-width: 100%;
	overflow-x: auto;
	-webkit-overflow-scrolling: touch;
}
.acb-brands-table {
	width: 100%;
	min-width: 280px;
	border-collapse: collapse;
	table-layout: fixed;
}
.acb-brands-table thead th {
	background: #FF2E2E;
	color: #111827;
	font-weight: 700;
	font-size: clamp(0.9375rem, 2.6vw, 1rem);
	padding: 14px 16px;
	text-align: center;
	border: 1px solid #2a2a2a;
}
.acb-brands-table tbody td {
	color: #ffffff;
	font-size: clamp(0.875rem, 2.5vw, 0.975rem);
	line-height: 1.45;
	padding: 14px 16px;
	text-align: center;
	vertical-align: middle;
	border: 1px solid #2a2a2a;
	background: transparent;
	overflow-wrap: anywhere;
}
@media (max-width: 767px) {
	.acb-brands-choose-section {
		padding: 0 12px 28px;
	}
	.acb-brands-choose-inner {
		padding: 28px 16px 32px;
		border-radius: 12px;
	}
	.acb-brands-table thead th,
	.acb-brands-table tbody td {
		padding: 10px 8px;
		font-size: 0.8125rem;
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
<script id="acb-brands-choose-inject">
(function () {
	'use strict';
	if (!document.body.classList.contains('home') || document.getElementById('acb-brands-choose-section')) {
		return;
	}
	var order = document.querySelector('.acb-order-section');
	if (!order) {
		return;
	}
	var block = order.closest('.e-con.e-parent') || order.closest('.e-con') || order.closest('.elementor-element');
	if (!block || !block.parentNode) {
		return;
	}
	var html = <?php echo wp_json_encode( <<<'HTML'
<section class="acb-brands-choose-section" id="acb-brands-choose-section" aria-labelledby="acb-brands-choose-heading">
<div class="acb-brands-choose-inner">
<h2 class="acb-brands-choose-heading" id="acb-brands-choose-heading">Why Brands Choose America Custom Boxes</h2>
<hr class="acb-brands-choose-rule" aria-hidden="true" />
<p class="acb-brands-choose-intro">We don't just sell boxes — we build brand identities. Here's what thousands of American businesses trust us for:</p>
<div class="acb-brands-table-wrap">
<table class="acb-brands-table">
<thead><tr><th scope="col">What You Get</th><th scope="col">What You Get</th></tr></thead>
<tbody>
<tr><td>20% first-order discount</td><td>600+ packaging solutions</td></tr>
<tr><td>Free professional design</td><td>Free die &amp; plate setup</td></tr>
<tr><td>No stress over minimums (just 100 boxes)</td><td>Free 1-color printing</td></tr>
<tr><td>Eco-friendly &amp; sustainable materials</td><td>Nationwide free shipping</td></tr>
<tr><td>Flexible, transparent pricing</td><td>24/7 online support</td></tr>
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
	if (!section) {
		return;
	}
	block.parentNode.insertBefore(section, block.nextSibling);
})();
</script>
		<?php
	},
	105
);
