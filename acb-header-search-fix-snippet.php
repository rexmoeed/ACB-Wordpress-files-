<?php
/**
 * ACB Header Search Fix — ElementsKit search modal (desktop + mobile).
 * Does not change header layout; only clickability + modal stacking + JS fallback.
 */
add_action(
	'wp_head',
	static function () {
		?>
<style id="acb-header-search-fix">
/* Keep modal above header / offcanvas; do not alter header flex layout */
.mfp-bg,
.mfp-wrap,
.mfp-container {
	z-index: 100010 !important;
}
.mfp-wrap .ekit_modal-searchPanel,
.mfp-wrap .ekit-search-panel {
	pointer-events: auto !important;
}
/* Reliable tap target on mobile without moving other header items */
@media (max-width: 767px) {
	.elementor-106 .elementor-element-5544ec35 .ekit_navsearch-button {
		position: relative !important;
		z-index: 25 !important;
		pointer-events: auto !important;
		cursor: pointer !important;
		min-width: 40px !important;
		min-height: 40px !important;
		align-items: center !important;
		justify-content: center !important;
		-webkit-tap-highlight-color: transparent;
	}
}
</style>
		<?php
	},
	103
);

add_action(
	'wp_footer',
	static function () {
		?>
<script id="acb-header-search-fix">
(function () {
	var MODAL_ID = 'ekit_modal-popup-5544ec35';
	var BTN_SEL = '.ekit_navsearch-button, a[href="#' + MODAL_ID + '"]';

	function openSearchModal(e) {
		var btn = e.target && e.target.closest ? e.target.closest(BTN_SEL) : null;
		if (!btn) {
			return;
		}
		if (!document.getElementById(MODAL_ID)) {
			return;
		}
		e.preventDefault();
		e.stopPropagation();

		if (window.jQuery && jQuery.magnificPopup) {
			jQuery.magnificPopup.close();
			jQuery.magnificPopup.open({
				items: { src: '#' + MODAL_ID, type: 'inline' },
				mainClass: 'mfp-fade',
				removalDelay: 280,
				closeBtnInside: true,
				callbacks: {
					open: function () {
						setTimeout(function () {
							var inp = document.querySelector(
								'.mfp-content .ekit_search-field, #' + MODAL_ID + ' .ekit_search-field'
							);
							if (inp) {
								inp.focus();
							}
						}, 320);
					},
				},
			});
		}
	}

	document.addEventListener('click', openSearchModal, true);
})();
</script>
		<?php
	},
	103
);
