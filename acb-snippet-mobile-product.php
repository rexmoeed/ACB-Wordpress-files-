<?php
add_action(
	'wp_head',
	static function () {
		if ( ! function_exists( 'is_product' ) || ! is_product() ) {
			return;
		}
		?>
<style id="acb-single-product-mobile-css">
@media (max-width:767px){
.single-product .elementor-464 .elementor-element-5cfb8e5,
.single-product .elementor-464 .elementor-element-5cfb8e5 > .e-con-inner {
	display: grid !important;
	grid-template-columns: 1fr 1fr;
	grid-template-areas:
		"gallery title"
		"gallery desc"
		"form form"
		"specs specs";
	gap: 16px;
	width: 100% !important;
	--flex-direction: column !important;
}
.single-product .elementor-464 .elementor-element-5cfb8e5 > .elementor-element-dd570a0,
.single-product .elementor-464 .elementor-element-5cfb8e5 > .elementor-element-ae0988c,
.single-product .elementor-464 .elementor-element-5cfb8e5 .elementor-element-dd570a0 > .e-con-inner,
.single-product .elementor-464 .elementor-element-5cfb8e5 .elementor-element-ae0988c > .e-con-inner {
	display: contents !important;
}
.single-product .elementor-464 .elementor-element-729f645 { grid-area: gallery; width: 100% !important; }
.single-product .elementor-464 .elementor-element-63ce159 { grid-area: title; width: 100% !important; }
.single-product .elementor-464 .elementor-element-adf987d { grid-area: desc; width: 100% !important; }
.single-product .elementor-464 .elementor-element-acbquote1 { grid-area: form; width: 100% !important; max-width: 100% !important; }
.single-product .elementor-464 .elementor-element-acbspecs1 { grid-area: specs; width: 100% !important; max-width: 100% !important; }
.single-product .elementor-464 .elementor-element-ae0988c .elementor-heading-title { font-size: 22px !important; line-height: 1.25 !important; word-break: break-word; }
.single-product .elementor-464 .elementor-element-adf987d .woocommerce-product-details__short-description { font-size: 15px; line-height: 1.6; }
.elementor-widget-woocommerce-product-images .woocommerce-product-gallery__image img { max-height: 340px; }
.elementor-widget-woocommerce-product-images .flex-control-thumbs li,
.elementor-widget-woocommerce-product-images .flex-control-thumbs li img { width: 64px !important; height: 64px !important; }
.acb-pc-specs-sidebar .acb-pc-specs-grid { grid-template-columns: 1fr !important; }
.single-product .woocommerce-breadcrumb { font-size: 12px; line-height: 1.5; word-break: break-word; }
.single-product .elementor-464 .elementor-element-e45c370,
.single-product .elementor-464 .elementor-element-e45c370 > .e-con-inner { width: 100% !important; max-width: 100% !important; padding-left: 12px !important; padding-right: 12px !important; }
.single-product .elementor-464 .elementor-element-17798a4 { padding-left: 12px !important; padding-right: 12px !important; }
.single-product .related.products ul.products { grid-template-columns: repeat(2, minmax(0, 1fr)) !important; gap: 12px !important; }
}
@media (max-width:480px){
.single-product .related.products ul.products { grid-template-columns: 1fr !important; }
.acb-qf-badges { grid-template-columns: 1fr !important; }
}
</style>
		<?php
	},
	100
);
