<?php
/**
 * Instant Quote — email handler for all .acb-qf-form forms (single product + archive).
 * Deploy via Code Snippets: "Instant Quote"
 */
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

add_action(
	'plugins_loaded',
	static function () {
		remove_action( 'wp_ajax_acb_submit_instant_quote', 'acb_handle_instant_quote' );
		remove_action( 'wp_ajax_nopriv_acb_submit_instant_quote', 'acb_handle_instant_quote' );
	},
	999
);

add_action( 'wp_ajax_acb_submit_instant_quote', 'acb_instant_quote_handle_submission' );
add_action( 'wp_ajax_nopriv_acb_submit_instant_quote', 'acb_instant_quote_handle_submission' );

add_action( 'wp_ajax_submit_instant_quote', 'acb_instant_quote_handle_submission' );
add_action( 'wp_ajax_nopriv_submit_instant_quote', 'acb_instant_quote_handle_submission' );

/**
 * Homepage/other pages embed quote form HTML in Elementor; inline JS expects these globals.
 */
add_action(
	'wp_enqueue_scripts',
	static function () {
		if ( is_admin() ) {
			return;
		}
		$needs_form = ( function_exists( 'is_front_page' ) && is_front_page() )
			|| ( function_exists( 'is_product' ) && is_product() )
			|| ( function_exists( 'is_product_taxonomy' ) && is_product_taxonomy() )
			|| ( function_exists( 'is_shop' ) && is_shop() )
			|| ( function_exists( 'is_page' ) && ( is_page( 'contact-us' ) || is_page( 'get-quote' ) || is_page( 'about-us' ) || is_page( 88 ) || is_page( 82 ) ) );
		if ( ! $needs_form ) {
			return;
		}
		$is_about = function_exists( 'is_page' ) && ( is_page( 'about-us' ) || is_page( 82 ) );
		if ( ! $is_about ) {
			wp_enqueue_style(
				'acb-quote-form-css',
				content_url( 'mu-plugins/acb-quote-form.css' ),
				array(),
				'1.0.4'
			);
		}
		wp_enqueue_script(
			'acb-quote-form-js',
			content_url( 'mu-plugins/acb-quote-form.js' ),
			array(),
			'1.0.4',
			true
		);
		wp_register_script( 'acb-quote-form-globals', false, array( 'acb-quote-form-js' ), '1.0.2', true );
		wp_enqueue_script( 'acb-quote-form-globals' );
		$inline = 'window.acbQuoteFormNonce=' . wp_json_encode( wp_create_nonce( 'acb_instant_quote' ) ) . ';'
			. 'window.acbQuoteFormAjax=' . wp_json_encode( admin_url( 'admin-ajax.php' ) ) . ';'
			. 'window.acbQuoteFormConfig=window.acbQuoteFormConfig||{ajax:window.acbQuoteFormAjax,nonce:window.acbQuoteFormNonce};';
		wp_add_inline_script( 'acb-quote-form-globals', $inline, 'before' );
	},
	5
);

function acb_instant_quote_capture_mail_error( $wp_error ) {
	$GLOBALS['acb_instant_quote_last_mail_error'] = $wp_error;
	if ( is_wp_error( $wp_error ) ) {
		error_log( '[Instant Quote] wp_mail failed: ' . $wp_error->get_error_message() );
	}
}
add_action( 'wp_mail_failed', 'acb_instant_quote_capture_mail_error' );

function acb_instant_quote_verify_nonce(): bool {
	if ( isset( $_POST['quote_nonce'] ) && wp_verify_nonce( sanitize_text_field( wp_unslash( $_POST['quote_nonce'] ) ), 'acb_instant_quote' ) ) {
		return true;
	}
	if ( isset( $_POST['quote_nonce'] ) && wp_verify_nonce( sanitize_text_field( wp_unslash( $_POST['quote_nonce'] ) ), 'quote_form_nonce' ) ) {
		return true;
	}
	return false;
}

/**
 * Branded HTML + plain-text bodies for sales notification.
 *
 * @param array<string, string> $data
 * @return array{html: string, plain: string}
 */
function acb_instant_quote_email_bodies( array $data, bool $embedded_logo = false ): array {
	$logo_url = 'https://americacustomboxes.com/wp-content/uploads/2026/07/Acb-logo-landscape.webp';
	$site     = 'https://americacustomboxes.com';
	$red      = '#FF2E2E';
	$blue     = '#0049E9';
	$submitted = gmdate( 'F j, Y \a\t g:i a T' );

	$full_name    = $data['full_name'];
	$email        = $data['email'];
	$phone        = $data['phone'] ?: 'Not provided';
	$product_name = $data['product_name'] ?: 'Not specified';
	$quantity     = $data['quantity'] ?: 'Not selected';
	$message      = $data['message'] ?: 'None provided';

	$logo_src = $embedded_logo ? 'cid:acb_logo' : $logo_url;

	$plain  = "New instant quote request\n\n";
	$plain .= "CONTACT\nFull Name: {$full_name}\nEmail: {$email}\nPhone: {$phone}\n\n";
	$plain .= "PACKAGING\nProduct: {$product_name}\nQuantity: {$quantity}\n\n";
	$plain .= "MESSAGE\n{$message}\n\n";
	$plain .= "Submitted: {$submitted}\n{$site}";

	$row = static function ( string $label, string $value ) use ( $blue ): string {
		$label_esc = esc_html( $label );
		$value_esc = nl2br( esc_html( $value ) );
		return '<tr><td style="padding:10px 14px;border-bottom:1px solid #eee;width:38%;color:' . $blue . ';font-weight:700;font-size:13px;vertical-align:top;">'
			. $label_esc . '</td><td style="padding:10px 14px;border-bottom:1px solid #eee;color:#333;font-size:14px;line-height:1.5;">'
			. $value_esc . '</td></tr>';
	};

	$html = '<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head><body style="margin:0;padding:0;background:#f0f4ff;font-family:Arial,Helvetica,sans-serif;">';
	$html .= '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f0f4ff;padding:24px 12px;"><tr><td align="center">';
	$html .= '<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 8px 32px rgba(0,73,233,0.12);">';

	$html .= '<tr><td style="background:linear-gradient(135deg,#FFF5F5 0%,#F5F8FF 100%);padding:28px 24px 20px;text-align:center;border-bottom:3px solid ' . $red . ';">';
	$html .= '<a href="' . esc_url( $site ) . '" style="text-decoration:none;display:inline-block;">';
	$html .= '<img src="' . esc_attr( $logo_src ) . '" alt="America Custom Boxes" width="240" style="max-width:240px;width:240px;height:auto;display:block;margin:0 auto;border:0;outline:none;text-decoration:none;">';
	$html .= '</a></td></tr>';

	$html .= '<tr><td style="padding:24px 28px 8px;"><h1 style="margin:0 0 8px;font-size:22px;line-height:1.3;color:#111;">New <span style="color:' . $red . ';">Instant Quote</span> Request</h1>';
	$html .= '<p style="margin:0;font-size:14px;color:#666;">A visitor submitted the quote form on your website.</p></td></tr>';

	$html .= '<tr><td style="padding:8px 28px 4px;"><p style="margin:0 0 8px;font-size:12px;font-weight:700;letter-spacing:0.06em;text-transform:uppercase;color:' . $blue . ';">Contact information</p>';
	$html .= '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #e8ecf4;border-radius:8px;overflow:hidden;">';
	$html .= $row( 'Full name', $full_name ) . $row( 'Email', $email ) . $row( 'Phone', $phone );
	$html .= '</table></td></tr>';

	$html .= '<tr><td style="padding:16px 28px 4px;"><p style="margin:0 0 8px;font-size:12px;font-weight:700;letter-spacing:0.06em;text-transform:uppercase;color:' . $blue . ';">Packaging details</p>';
	$html .= '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #e8ecf4;border-radius:8px;overflow:hidden;">';
	$html .= $row( 'Product / category', $product_name ) . $row( 'Quantity', $quantity );
	$html .= '</table></td></tr>';

	$html .= '<tr><td style="padding:16px 28px 4px;"><p style="margin:0 0 8px;font-size:12px;font-weight:700;letter-spacing:0.06em;text-transform:uppercase;color:' . $blue . ';">Additional message</p>';
	$html .= '<div style="border:1px solid #e8ecf4;border-radius:8px;padding:14px 16px;background:#FAFBFF;font-size:14px;line-height:1.6;color:#333;">' . nl2br( esc_html( $message ) ) . '</div></td></tr>';

	$html .= '<tr><td style="padding:20px 28px 28px;"><p style="margin:0;font-size:12px;color:#888;">Submitted ' . esc_html( $submitted ) . ' · <a href="' . esc_url( $site ) . '" style="color:' . $blue . ';text-decoration:none;">americacustomboxes.com</a></p>';
	$html .= '<p style="margin:12px 0 0;font-size:12px;color:#888;">Reply directly to this email to reach the customer.</p></td></tr>';

	$html .= '</table></td></tr></table></body></html>';

	return array(
		'html'  => $html,
		'plain' => $plain,
	);
}

function acb_instant_quote_handle_submission() {
	if ( ! acb_instant_quote_verify_nonce() ) {
		wp_send_json_error( array( 'message' => 'Security check failed. Please refresh the page and try again.' ) );
	}

	if ( function_exists( 'acb_spam_guard' ) ) {
		acb_spam_guard( 'instant_quote' );
	}

	$full_name    = sanitize_text_field( wp_unslash( $_POST['full_name'] ?? '' ) );
	$email        = sanitize_email( wp_unslash( $_POST['email'] ?? '' ) );
	$phone        = sanitize_text_field( wp_unslash( $_POST['phone'] ?? '' ) );
	$quantity     = sanitize_text_field( wp_unslash( $_POST['quantity'] ?? '' ) );
	$message      = sanitize_textarea_field( wp_unslash( $_POST['message'] ?? '' ) );
	$product_name = sanitize_text_field( wp_unslash( $_POST['product_name'] ?? '' ) );

	if ( function_exists( 'acb_form_require_name_email_phone' ) ) {
		acb_form_require_name_email_phone( $full_name, $email, $phone );
	} else {
		if ( empty( $full_name ) || empty( $email ) || empty( $phone ) ) {
			wp_send_json_error( array( 'message' => 'Please fill in your full name, email address, and phone number.' ) );
		}
		if ( ! is_email( $email ) ) {
			wp_send_json_error( array( 'message' => 'Please provide a valid email address.' ) );
		}
	}

	$to      = 'sales@americacustomboxes.com';
	$subject = 'New Instant Quote — ' . $full_name . ( $product_name ? ' (' . $product_name . ')' : '' );

	$bodies = acb_instant_quote_email_bodies(
		array(
			'full_name'    => $full_name,
			'email'        => $email,
			'phone'        => $phone,
			'product_name' => $product_name,
			'quantity'     => $quantity,
			'message'      => $message,
		),
		true
	);

	$logo_url  = 'https://americacustomboxes.com/wp-content/uploads/2026/07/Acb-logo-landscape.webp';
	$logo_path = WP_CONTENT_DIR . '/uploads/2026/07/Acb-logo-landscape.webp';
	$embed_logo = static function ( $phpmailer ) use ( $logo_path, $logo_url ) {
		if ( file_exists( $logo_path ) ) {
			$phpmailer->AddEmbeddedImage( $logo_path, 'acb_logo', 'Acb-logo-landscape.webp' );
			return;
		}
		// Fallback: fetch from media library URL to temp (remote logo).
		$tmp = download_url( $logo_url );
		if ( ! is_wp_error( $tmp ) && file_exists( $tmp ) ) {
			$phpmailer->AddEmbeddedImage( $tmp, 'acb_logo', 'Acb-logo-landscape.webp' );
		}
	};
	add_action( 'phpmailer_init', $embed_logo, 10, 1 );

	$headers = array(
		'Content-Type: text/html; charset=UTF-8',
		'Reply-To: ' . $full_name . ' <' . $email . '>',
	);

	$attachments = array();
	$tmp_files   = array();

	$upload_fn = function_exists( 'acb_form_save_image_upload' ) ? 'acb_form_save_image_upload' : null;
	if ( $upload_fn ) {
		$result = $upload_fn( 'artwork_file' );
		if ( empty( $result['ok'] ) ) {
			wp_send_json_error( array( 'message' => $result['error'] ?? 'Invalid upload.' ) );
		}
		if ( ! empty( $result['path'] ) ) {
			$attachments[] = $result['path'];
			$tmp_files[]   = $result['path'];
		}
	}

	$GLOBALS['acb_instant_quote_last_mail_error'] = null;

	$sent = wp_mail( $to, $subject, $bodies['html'], $headers, $attachments );

	remove_action( 'phpmailer_init', $embed_logo, 10 );

	foreach ( $tmp_files as $tmp ) {
		if ( file_exists( $tmp ) ) {
			wp_delete_file( $tmp );
		}
	}

	if ( $sent ) {
		wp_send_json_success( array( 'message' => 'Thank you! Your quote request has been sent. We will get back to you shortly.' ) );
	}

	$response = array( 'message' => 'Failed to send email. Please try again or email sales@americacustomboxes.com directly.' );
	$mail_error = $GLOBALS['acb_instant_quote_last_mail_error'] ?? null;
	if ( defined( 'WP_DEBUG' ) && WP_DEBUG && is_wp_error( $mail_error ) ) {
		$response['message'] = 'Failed to send email: ' . $mail_error->get_error_message();
	}

	wp_send_json_error( $response );
}
