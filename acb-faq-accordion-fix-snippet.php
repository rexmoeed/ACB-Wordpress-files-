<?php
/**
 * ACB FAQ Accordion Fix — restores open/close without changing FAQ layout/CSS structure.
 */
add_action(
	'wp_head',
	static function () {
		?>
<style id="acb-faq-accordion-fix">
/* Open height via class (JS no longer depends on scrollHeight inline beating stylesheet) */
.acb-faq-section .acb-faq-item.is-open .acb-faq-answer-wrap {
	max-height: 1200px !important;
}
</style>
		<?php
	},
	104
);

add_action(
	'wp_footer',
	static function () {
		?>
<script id="acb-faq-accordion-fix">
(function () {
	'use strict';

	function toggleItem(btn) {
		var item = btn.closest('.acb-faq-item');
		var root = btn.closest('.acb-faq-section');
		if (!item || !root) {
			return;
		}

		var willOpen = !item.classList.contains('is-open');
		root.querySelectorAll('.acb-faq-item').forEach(function (other) {
			other.classList.remove('is-open');
			var otherBtn = other.querySelector('.acb-faq-question');
			if (otherBtn) {
				otherBtn.setAttribute('aria-expanded', 'false');
			}
			var otherWrap = other.querySelector('.acb-faq-answer-wrap');
			if (otherWrap) {
				otherWrap.style.removeProperty('max-height');
			}
		});

		if (willOpen) {
			item.classList.add('is-open');
			btn.setAttribute('aria-expanded', 'true');
		}
	}

	document.addEventListener(
		'click',
		function (e) {
			var btn = e.target.closest('.acb-faq-section .acb-faq-question');
			if (!btn) {
				return;
			}
			e.preventDefault();
			e.stopPropagation();
			toggleItem(btn);
		},
		true
	);

	/* If Elementor injects the FAQ block after mu-plugin init, clear stale guard once. */
	function retryInit() {
		if (typeof window.acbFaqAccordionInit !== 'function') {
			return;
		}
		document.querySelectorAll('.acb-faq-section[data-acb-faq-init="1"]').forEach(function (root) {
			root.removeAttribute('data-acb-faq-init');
		});
		window.acbFaqAccordionInit(document);
	}

	window.addEventListener('load', retryInit);
	if (window.jQuery) {
		jQuery(window).on('elementor/frontend/init', retryInit);
	}
})();
</script>
		<?php
	},
	104
);
