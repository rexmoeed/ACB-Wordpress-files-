<?php
/**
 * ACB Archive Category Content — styled sections matching single product ACF output.
 * Deploy to Code Snippets #17.
 */
add_action(
	'init',
	static function () {
		remove_shortcode( 'acb_archive_category_description' );
		add_shortcode( 'acb_archive_category_description', 'acb_snippet_archive_category_description' );
	},
	99
);

function acb_snippet_archive_category_description(): string {
	if ( ! function_exists( 'is_product_taxonomy' ) || ! is_product_taxonomy() ) {
		return '';
	}
	$term = get_queried_object();
	if ( ! $term instanceof WP_Term || empty( $term->description ) ) {
		return '';
	}
	return acb_snippet_render_archive_content( $term->description );
}

/**
 * @param array<string,mixed> $data Structured archive content.
 */
function acb_snippet_render_archive_structured( array $data ): string {
	$intro          = isset( $data['intro'] ) && is_array( $data['intro'] ) ? $data['intro'] : array();
	$why_title      = isset( $data['why_title'] ) ? (string) $data['why_title'] : '';
	$why_items      = isset( $data['why_items'] ) && is_array( $data['why_items'] ) ? $data['why_items'] : array();
	$styles         = isset( $data['styles'] ) && is_array( $data['styles'] ) ? $data['styles'] : array();
	$customization  = isset( $data['customization'] ) && is_array( $data['customization'] ) ? $data['customization'] : array();
	$sustainability = isset( $data['sustainability'] ) ? trim( (string) $data['sustainability'] ) : '';
	$faq            = isset( $data['faq'] ) && is_array( $data['faq'] ) ? $data['faq'] : array();

	ob_start();
	echo '<div class="acb-pc acb-archive-desc" id="acb-archive-content">';

	if ( $intro ) {
		echo '<section class="acb-pc-section acb-pc-intro">';
		foreach ( $intro as $paragraph ) {
			if ( ! is_string( $paragraph ) || '' === trim( $paragraph ) ) {
				continue;
			}
			echo '<p>' . esc_html( $paragraph ) . '</p>';
		}
		echo '</section>';
	}

	if ( $why_items ) {
		echo '<section class="acb-pc-section acb-pc-why">';
		echo '<h2 class="acb-pc-heading acb-pc-heading--blue">' . esc_html( $why_title ?: 'Why Choose Us?' ) . '</h2>';
		echo '<ul class="acb-pc-why-list">';
		foreach ( $why_items as $item ) {
			if ( ! is_array( $item ) ) {
				continue;
			}
			$label = isset( $item['label'] ) ? trim( (string) $item['label'] ) : '';
			$text  = isset( $item['text'] ) ? trim( (string) $item['text'] ) : '';
			if ( ! $label && ! $text ) {
				continue;
			}
			echo '<li class="acb-pc-why-item">';
			echo '<span class="acb-pc-why-icon" aria-hidden="true">&#10003;</span>';
			echo '<span class="acb-pc-why-text">';
			if ( $label ) {
				echo '<strong>' . esc_html( $label ) . ':</strong> ';
			}
			echo esc_html( $text );
			echo '</span></li>';
		}
		echo '</ul></section>';
	}

	if ( $styles ) {
		echo '<section class="acb-pc-section acb-pc-styles">';
		echo '<h2 class="acb-pc-heading acb-pc-heading--red">Popular Styles &amp; Options</h2>';
		echo '<div class="acb-pc-style-grid">';
		foreach ( $styles as $style ) {
			if ( ! is_array( $style ) || empty( $style['title'] ) ) {
				continue;
			}
			echo '<div class="acb-pc-style-card">';
			echo '<h3 class="acb-pc-style-title">' . esc_html( (string) $style['title'] ) . '</h3>';
			if ( ! empty( $style['description'] ) ) {
				echo '<p class="acb-pc-style-desc">' . esc_html( (string) $style['description'] ) . '</p>';
			}
			echo '</div>';
		}
		echo '</div></section>';
	}

	if ( $customization ) {
		echo '<section class="acb-pc-section acb-pc-custom">';
		echo '<h2 class="acb-pc-heading acb-pc-heading--blue">Customization Options</h2>';
		echo '<div class="acb-pc-custom-grid">';
		foreach ( $customization as $opt ) {
			if ( ! is_array( $opt ) || empty( $opt['label'] ) ) {
				continue;
			}
			echo '<div class="acb-pc-custom-item">';
			echo '<span class="acb-pc-custom-label">' . esc_html( (string) $opt['label'] ) . '</span>';
			echo '<span class="acb-pc-custom-value">' . esc_html( (string) ( $opt['content'] ?? '' ) ) . '</span>';
			echo '</div>';
		}
		echo '</div></section>';
	}

	if ( $sustainability ) {
		echo '<section class="acb-pc-section acb-pc-sustain">';
		echo '<h2 class="acb-pc-heading acb-pc-heading--red">Sustainable Packaging Options</h2>';
		echo '<p class="acb-pc-sustain-text">' . esc_html( $sustainability ) . '</p>';
		echo '</section>';
	}

	if ( $faq && function_exists( 'acb_render_faq_accordion' ) ) {
		echo '<section class="acb-pc-section acb-pc-faq">';
		echo acb_render_faq_accordion( $faq ); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped
		echo '</section>';
	}

	echo '</div>';
	return (string) ob_get_clean();
}

function acb_snippet_parse_archive_json( string $raw ): ?array {
	if ( preg_match( '/<!--acb-archive-v2-->(.+?)<!--\/acb-archive-v2-->/s', $raw, $m ) ) {
		$data = json_decode( html_entity_decode( $m[1], ENT_QUOTES | ENT_HTML5, 'UTF-8' ), true );
		return is_array( $data ) ? $data : null;
	}
	return null;
}

function acb_snippet_render_archive_content( string $raw ): string {
	$structured = acb_snippet_parse_archive_json( $raw );
	if ( is_array( $structured ) ) {
		return acb_snippet_render_archive_structured( $structured );
	}

	$raw  = str_replace( array( '</p>', '<br />', '<br>', '<br/>', '</li>', '</div>' ), "\n", $raw );
	$text = html_entity_decode( wp_strip_all_tags( str_replace( array( "\r\n", "\r" ), "\n", $raw ) ) );
	$lines = array();
	foreach ( preg_split( '/\n\s*\n/', $text ) as $chunk ) {
		foreach ( preg_split( '/\n/', trim( $chunk ) ) as $line ) {
			$line = trim( $line );
			if ( '' !== $line ) {
				$lines[] = $line;
			}
		}
	}

	$intro     = array();
	$why_title = '';
	$why_items = array();
	$mode      = 'intro';

	foreach ( $lines as $line ) {
		if ( preg_match( '/^Why Choose/i', $line ) ) {
			$mode      = 'why';
			$why_title = $line;
			continue;
		}
		if ( preg_match( '/^Key Benefits/i', $line ) ) {
			break;
		}
		if ( 'intro' === $mode && strlen( $line ) > 40 ) {
			$intro[] = $line;
			continue;
		}
		if ( 'why' === $mode && preg_match( '/^(.+?)\s*[\x{2014}\x{2013}\-]\s*(.+)$/u', $line, $m ) ) {
			$why_items[] = array( 'label' => trim( $m[1] ), 'text' => trim( $m[2] ) );
		}
	}

	return acb_snippet_render_archive_structured(
		array(
			'intro'     => $intro,
			'why_title' => $why_title,
			'why_items' => $why_items,
			'styles'    => array(),
			'customization' => array(),
			'sustainability' => '',
			'faq'       => array(),
		)
	);
}
