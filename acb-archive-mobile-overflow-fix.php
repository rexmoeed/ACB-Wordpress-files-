<?php
/**
 * Archive mobile overflow + quote form layout fix (snippet deploy source).
 */
add_action(
	'wp_head',
	static function () {
		if ( ! function_exists( 'is_product_taxonomy' ) || ! is_product_taxonomy() ) {
			return;
		}
		?>
<style id="acb-archive-mobile-overflow-fix">
@media (max-width: 767px) {
	body.tax-product_cat .elementor-location-archive.elementor-296,
	body.tax-product_cat .elementor-location-archive.elementor-296 .elementor-element-b3f39ff,
	body.tax-product_cat .elementor-location-archive.elementor-296 .elementor-element-b3f39ff > .e-con-inner {
		overflow-x: clip;
		max-width: 100%;
	}

	.elementor-location-archive .elementor-element-c1desc,
	.elementor-location-archive .elementor-element-acbarchq1 {
		width: 100% !important;
		max-width: 100% !important;
		min-width: 0 !important;
		--width: 100% !important;
		--container-widget-width: 100% !important;
	}

	.elementor-location-archive .elementor-element-c1desc .elementor-widget-container,
	.elementor-location-archive .elementor-element-c1desc .elementor-shortcode,
	.elementor-location-archive .elementor-element-acbarchq1 .elementor-widget-container,
	.elementor-location-archive .elementor-element-acbarchq1 .elementor-shortcode {
		width: 100% !important;
		max-width: 100% !important;
		min-width: 0 !important;
		padding-left: 0 !important;
		padding-right: 0 !important;
		margin-left: 0 !important;
		margin-right: 0 !important;
	}

	.elementor-location-archive .acb-archive-desc.acb-pc,
	.elementor-location-archive .acb-pc {
		max-width: 100% !important;
		overflow-wrap: anywhere;
	}

	.elementor-location-archive .acb-faq-section {
		max-width: 100% !important;
		width: 100% !important;
		padding: 0 !important;
	}

	.elementor-location-archive .acb-faq-heading {
		font-size: 24px !important;
		line-height: 1.2 !important;
	}

	.elementor-location-archive .acb-faq-question {
		font-size: 14px !important;
		gap: 10px !important;
		padding: 14px 0 !important;
	}

	.elementor-location-archive .acb-archive-quote-band {
		width: 100% !important;
		max-width: 100% !important;
		margin: 0 !important;
		padding: 0 !important;
		overflow: hidden;
	}

	.elementor-location-archive .acb-quote-section--with-image {
		display: flex !important;
		flex-direction: column !important;
		width: 100% !important;
		max-width: 100% !important;
		min-width: 0 !important;
		padding: 16px 0 24px !important;
		gap: 16px !important;
		margin: 0 !important;
		box-sizing: border-box;
	}

	.elementor-location-archive .acb-quote-section--with-image .acb-quote-form-col,
	.elementor-location-archive .acb-quote-section--with-image .acb-quote-image-col {
		width: 100% !important;
		max-width: 100% !important;
		min-width: 0 !important;
	}

	.elementor-location-archive .acb-qf-wrap {
		width: 100% !important;
		max-width: 100% !important;
		min-width: 0 !important;
		padding: 18px 14px !important;
		box-sizing: border-box;
	}

	.elementor-location-archive .acb-qf-field,
	.elementor-location-archive .acb-qf-file-row {
		width: 100% !important;
		max-width: 100% !important;
		min-width: 0 !important;
	}

	.elementor-location-archive .acb-qf-icon {
		width: 42px !important;
		min-width: 42px !important;
	}

	.elementor-location-archive .acb-qf-field input,
	.elementor-location-archive .acb-qf-field select,
	.elementor-location-archive .acb-qf-field textarea {
		min-width: 0 !important;
		font-size: 14px !important;
	}

	.elementor-location-archive .acb-qf-file-label {
		font-size: 11px !important;
		padding: 0 6px !important;
		min-width: 0 !important;
	}

	.elementor-location-archive .acb-qf-file-btn {
		padding: 0 10px !important;
		font-size: 11px !important;
		height: 50px;
		flex-shrink: 0;
	}

	.elementor-location-archive .acb-qf-badges {
		grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
		gap: 8px !important;
	}

	.elementor-location-archive .acb-quote-image-col {
		min-height: 180px !important;
		max-height: 220px !important;
		width: 100% !important;
	}
}

@media (max-width: 480px) {
	.elementor-location-archive .acb-qf-badges {
		grid-template-columns: 1fr !important;
	}
}
</style>
		<?php
	},
	101
);
