<?php
define( 'WP_USE_THEMES', false );
require __DIR__ . '/app/public/wp-load.php';

header( 'Content-Type: application/json' );

$parent = get_term_by( 'slug', 'by-industry', 'product_cat' );
$terms  = get_terms(
	array(
		'taxonomy'   => 'product_cat',
		'parent'     => (int) $parent->term_id,
		'hide_empty' => false,
		'orderby'    => 'count',
		'order'      => 'DESC',
	)
);

echo wp_json_encode(
	array(
		'parent'       => $parent,
		'is_error'     => is_wp_error( $terms ),
		'error'        => is_wp_error( $terms ) ? $terms->get_error_message() : null,
		'terms_count'  => is_array( $terms ) ? count( $terms ) : 0,
		'terms'        => is_array( $terms ) ? array_map(
			function ( $t ) {
				return array( 'id' => $t->term_id, 'name' => $t->name, 'slug' => $t->slug, 'parent' => $t->parent, 'count' => $t->count );
			},
			$terms
		) : array(),
		'child_ids'    => get_term_children( (int) $parent->term_id, 'product_cat' ),
	),
	JSON_PRETTY_PRINT
);
