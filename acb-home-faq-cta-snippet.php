<?php
/**
 * Homepage only: post-FAQ CTA block (doc: Ready for Packaging That Sells?).
 */
add_action(
	'wp_head',
	static function () {
		if ( ! function_exists( 'is_front_page' ) || ! is_front_page() ) {
			return;
		}
		?>
<style id="acb-home-faq-cta-css">
.acb-home-faq-cta {
	width: 100%;
	max-width: 100%;
	box-sizing: border-box;
	font-family: 'Titillium Web', sans-serif;
	padding: 0 16px 40px;
	margin: 0 auto;
}
.acb-home-faq-cta *,
.acb-home-faq-cta *::before,
.acb-home-faq-cta *::after {
	box-sizing: border-box;
}
.acb-home-faq-cta-inner {
	max-width: 1200px;
	margin: 0 auto;
	background: #000000;
	border-radius: 15px;
	padding: 36px 32px 40px;
	color: #ffffff;
	overflow: hidden;
}
.acb-home-faq-cta-heading {
	color: #ff2e2e;
	font-size: clamp(1.35rem, 4vw, 1.85rem);
	font-weight: 700;
	line-height: 1.25;
	margin: 0 0 14px;
}
.acb-home-faq-cta-rule {
	border: 0;
	border-top: 1px solid rgba(255, 255, 255, 0.15);
	margin: 0 0 16px;
}
.acb-home-faq-cta-text {
	font-size: clamp(0.9375rem, 2.7vw, 1.02rem);
	line-height: 1.65;
	margin: 0 0 20px;
	color: #ffffff;
	max-width: 920px;
}
.acb-home-faq-cta-box {
	border: 2px solid #ff2e2e;
	border-radius: 12px;
	padding: 18px 20px;
	font-size: clamp(0.875rem, 2.5vw, 0.98rem);
	line-height: 1.6;
	color: #ffffff;
}
.acb-home-faq-cta-box strong {
	font-weight: 700;
	color: #ffffff;
}
.acb-home-faq-cta-actions {
	display: flex;
	flex-wrap: wrap;
	align-items: stretch;
	gap: 12px;
	margin-top: 14px;
}
.acb-home-faq-cta-btn {
	display: inline-flex;
	align-items: center;
	justify-content: center;
	gap: 6px;
	padding: 12px 20px;
	border-radius: 999px;
	font-size: clamp(0.8125rem, 2.4vw, 0.9375rem);
	font-weight: 700;
	line-height: 1.25;
	text-decoration: none;
	font-family: 'Titillium Web', sans-serif;
	border: 2px solid transparent;
	transition: background 0.2s ease, color 0.2s ease, border-color 0.2s ease, transform 0.2s ease;
	white-space: nowrap;
}
.acb-home-faq-cta-btn:hover,
.acb-home-faq-cta-btn:focus-visible {
	transform: translateY(-1px);
	outline: none;
}
.acb-home-faq-cta-btn--primary {
	background: #ff2e2e;
	color: #ffffff;
	border-color: #ff2e2e;
}
.acb-home-faq-cta-btn--primary:hover,
.acb-home-faq-cta-btn--primary:focus-visible {
	background: #ff5757;
	border-color: #ff5757;
	color: #ffffff;
}
.acb-home-faq-cta-btn--outline {
	background: #000000;
	color: #ffffff;
	border-color: #ffffff;
}
.acb-home-faq-cta-btn--outline:hover,
.acb-home-faq-cta-btn--outline:focus-visible {
	background: #ffffff;
	color: #000000;
	border-color: #ffffff;
}
@media (max-width: 600px) {
	.acb-home-faq-cta-inner {
		padding: 24px 16px 28px;
	}
	.acb-home-faq-cta-box {
		padding: 14px 14px;
	}
	.acb-home-faq-cta-actions {
		flex-direction: column;
		align-items: stretch;
	}
	.acb-home-faq-cta-btn {
		width: 100%;
		white-space: normal;
		text-align: center;
		padding: 12px 16px;
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
<script id="acb-home-faq-cta-inject">
(function () {
	'use strict';
	if (!document.body.classList.contains('home') || document.getElementById('acb-home-faq-cta')) {
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
	var html = <?php echo wp_json_encode( <<<'HTML'
<section class="acb-home-faq-cta" id="acb-home-faq-cta" aria-labelledby="acb-home-faq-cta-heading">
<div class="acb-home-faq-cta-inner">
<h2 class="acb-home-faq-cta-heading" id="acb-home-faq-cta-heading">Ready for Packaging That Sells?</h2>
<hr class="acb-home-faq-cta-rule" aria-hidden="true" />
<p class="acb-home-faq-cta-text">Tell us what you're packaging and we'll get you an instant quote. Free design, free setup, no minimums beyond 100 boxes, and free US shipping.</p>
<div class="acb-home-faq-cta-box">
<p style="margin:0;"><strong>Get your instant quote today.</strong></p>
<div class="acb-home-faq-cta-actions">
<a class="acb-home-faq-cta-btn acb-home-faq-cta-btn--primary" href="https://americacustomboxes.com/get-quote/">Get a Quote</a>
<a class="acb-home-faq-cta-btn acb-home-faq-cta-btn--outline" href="https://wa.me/12892032677" target="_blank" rel="noopener noreferrer">WhatsApp: +1 289-203-2677</a>
<a class="acb-home-faq-cta-btn acb-home-faq-cta-btn--outline" href="mailto:sales@americacustomboxes.com">sales@americacustomboxes.com</a>
</div>
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
	if (block.nextSibling) {
		block.parentNode.insertBefore(section, block.nextSibling);
	} else {
		block.parentNode.appendChild(section);
	}
})();
</script>
		<?php
	},
	107
);
