<?php
/**
 * Detailed Quote — AJAX email handler for /get-quote/ form.
 * Deploy via Code Snippets: "ACB Detailed Quote Form"
 */
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

add_action( 'wp_ajax_acb_submit_detailed_quote', 'acb_detailed_quote_handle_submission' );
add_action( 'wp_ajax_nopriv_acb_submit_detailed_quote', 'acb_detailed_quote_handle_submission' );
add_action( 'wp_ajax_submit_quote_form', 'acb_detailed_quote_handle_submission' );
add_action( 'wp_ajax_nopriv_submit_quote_form', 'acb_detailed_quote_handle_submission' );

add_action(
	'wp_enqueue_scripts',
	static function () {
		if ( is_admin() ) {
			return;
		}
		$on_quote = ( function_exists( 'is_page' ) && ( is_page( 'get-quote' ) || is_page( 88 ) ) );
		if ( ! $on_quote ) {
			return;
		}
		wp_register_script( 'acb-detailed-quote-globals', false, array(), '1.0.1', true );
		wp_enqueue_script( 'acb-detailed-quote-globals' );
		$inline = 'window.acbDetailedQuoteNonce=' . wp_json_encode( wp_create_nonce( 'acb_detailed_quote' ) ) . ';'
			. 'window.acbDetailedQuoteAjax=' . wp_json_encode( admin_url( 'admin-ajax.php' ) ) . ';'
			. 'window.quoteFormNonce=window.acbDetailedQuoteNonce;'
			. 'window.quoteFormAjax=window.acbDetailedQuoteAjax;';
		wp_add_inline_script( 'acb-detailed-quote-globals', $inline, 'before' );
	},
	5
);

function acb_detailed_quote_capture_mail_error( $wp_error ) {
	$GLOBALS['acb_detailed_quote_last_mail_error'] = $wp_error;
	if ( is_wp_error( $wp_error ) ) {
		error_log( '[Detailed Quote] wp_mail failed: ' . $wp_error->get_error_message() );
	}
}
add_action( 'wp_mail_failed', 'acb_detailed_quote_capture_mail_error' );

function acb_detailed_quote_verify_nonce(): bool {
	$nonce = isset( $_POST['quote_nonce'] ) ? sanitize_text_field( wp_unslash( $_POST['quote_nonce'] ) ) : '';
	if ( ! $nonce ) {
		return false;
	}
	return (bool) wp_verify_nonce( $nonce, 'acb_detailed_quote' )
		|| (bool) wp_verify_nonce( $nonce, 'acb_instant_quote' )
		|| (bool) wp_verify_nonce( $nonce, 'quote_form_nonce' );
}

/**
 * Branded HTML + plain-text bodies for sales notification.
 *
 * @param array<string, string> $data
 * @return array{html: string, plain: string}
 */
function acb_detailed_quote_email_bodies( array $data, bool $embedded_logo = false ): array {
	$logo_url  = 'https://americacustomboxes.com/wp-content/uploads/2026/07/Acb-logo-landscape.webp';
	$logo_src  = $embedded_logo ? 'cid:acb_logo' : $logo_url;
	$site      = 'https://americacustomboxes.com';
	$red       = '#FF2E2E';
	$blue      = '#0049E9';
	$submitted = gmdate( 'F j, Y \a\t g:i a T' );

	$row = static function ( string $label, string $value ) use ( $blue ): string {
		return '<tr><td style="padding:10px 14px;border-bottom:1px solid #eee;width:38%;color:' . $blue . ';font-weight:700;font-size:13px;vertical-align:top;">'
			. esc_html( $label ) . '</td><td style="padding:10px 14px;border-bottom:1px solid #eee;color:#333;font-size:14px;line-height:1.5;">'
			. nl2br( esc_html( $value ) ) . '</td></tr>';
	};

	$section = static function ( string $title, string $rows_html ) use ( $blue ): string {
		return '<tr><td style="padding:16px 28px 4px;"><p style="margin:0 0 8px;font-size:12px;font-weight:700;letter-spacing:0.06em;text-transform:uppercase;color:' . $blue . ';">'
			. esc_html( $title ) . '</p><table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #e8ecf4;border-radius:8px;overflow:hidden;">'
			. $rows_html . '</table></td></tr>';
	};

	$plain  = "New detailed quote request\n\n";
	$plain .= "CONTACT\nName: {$data['full_name']}\nCompany: {$data['company_name']}\nEmail: {$data['email']}\nPhone: {$data['phone']}\nCountry: {$data['country']}\n\n";
	$plain .= "PACKAGING\nStyle: {$data['box_style']}\nSize: {$data['length']} x {$data['width']} x {$data['height']} in\nQty: {$data['quantity']}\n\n";
	$plain .= "Material: {$data['material']} / {$data['thickness']}\nPrinting: {$data['printing']}\nFinishing: {$data['finishing']}\n\n";
	$plain .= "Notes:\n{$data['notes']}\n\nFiles: {$data['files_note']}\n\nSubmitted: {$submitted}\n{$site}";

	$html  = '<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>';
	$html .= '<body style="margin:0;padding:0;background:#f0f4ff;font-family:Arial,Helvetica,sans-serif;">';
	$html .= '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f0f4ff;padding:24px 12px;"><tr><td align="center">';
	$html .= '<table role="presentation" width="640" cellpadding="0" cellspacing="0" style="max-width:640px;width:100%;background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 8px 32px rgba(0,73,233,0.12);">';
	$html .= '<tr><td style="background:linear-gradient(135deg,#FFF5F5 0%,#F5F8FF 100%);padding:28px 24px 20px;text-align:center;border-bottom:3px solid ' . $red . ';">';
	$html .= '<a href="' . esc_url( $site ) . '" style="text-decoration:none;display:inline-block;">';
	$html .= '<img src="' . esc_attr( $logo_src ) . '" alt="America Custom Boxes" width="240" style="max-width:240px;width:240px;height:auto;display:block;margin:0 auto;border:0;outline:none;text-decoration:none;">';
	$html .= '</a></td></tr>';
	$html .= '<tr><td style="padding:24px 28px 8px;"><h1 style="margin:0 0 8px;font-size:22px;line-height:1.3;color:#111;">New <span style="color:' . $red . ';">Detailed Quote</span> Request</h1>';
	$html .= '<p style="margin:0;font-size:14px;color:#666;">Submitted from the Get Quote page.</p></td></tr>';
	$html .= $section(
		'1. Contact information',
		$row( 'Full name', $data['full_name'] ) . $row( 'Company', $data['company_name'] ) . $row( 'Email', $data['email'] ) . $row( 'Phone', $data['phone'] ) . $row( 'Country', $data['country'] )
	);
	$html .= $section(
		'2. Packaging details',
		$row( 'Box style', $data['box_style'] ) . $row( 'Dimensions (L×W×H in)', $data['length'] . ' × ' . $data['width'] . ' × ' . $data['height'] ) . $row( 'Quantity', $data['quantity'] )
	);
	$html .= $section(
		'3. Material & printing',
		$row( 'Material', $data['material'] ) . $row( 'Thickness', $data['thickness'] ?: 'Not specified' ) . $row( 'Printing', $data['printing'] ) . $row( 'Finishing', $data['finishing'] ?: 'None selected' ) . $row( 'Finishing other', $data['finishing_other'] ?: '—' )
	);
	$html .= '<tr><td style="padding:16px 28px 4px;"><p style="margin:0 0 8px;font-size:12px;font-weight:700;letter-spacing:0.06em;text-transform:uppercase;color:' . $blue . ';">Additional notes</p>';
	$html .= '<div style="border:1px solid #e8ecf4;border-radius:8px;padding:14px 16px;background:#FAFBFF;font-size:14px;line-height:1.6;color:#333;">' . nl2br( esc_html( $data['notes'] ?: 'None provided' ) ) . '</div></td></tr>';
	$html .= '<tr><td style="padding:16px 28px 4px;"><p style="margin:0 0 8px;font-size:12px;font-weight:700;letter-spacing:0.06em;text-transform:uppercase;color:' . $blue . ';">Uploaded files</p>';
	$html .= '<div style="border:1px solid #e8ecf4;border-radius:8px;padding:14px 16px;background:#FAFBFF;font-size:14px;color:#333;">' . esc_html( $data['files_note'] ) . '</div></td></tr>';
	$html .= '<tr><td style="padding:20px 28px 28px;"><p style="margin:0;font-size:12px;color:#888;">Submitted ' . esc_html( $submitted ) . ' · <a href="' . esc_url( $site ) . '" style="color:' . $blue . ';text-decoration:none;">americacustomboxes.com</a></p>';
	$html .= '<p style="margin:12px 0 0;font-size:12px;color:#888;">Reply directly to this email to reach the customer.</p></td></tr>';
	$html .= '</table></td></tr></table></body></html>';

	return array( 'html' => $html, 'plain' => $plain );
}

/**
 * @deprecated Use acb_form_save_image_upload() from ACB Spam Protection snippet.
 * @return array{ok:bool,path?:string,error?:string}
 */
function acb_detailed_quote_save_upload( string $field ): array {
	if ( function_exists( 'acb_form_save_image_upload' ) ) {
		return acb_form_save_image_upload( $field );
	}
	return array( 'ok' => true, 'path' => null );
}

function acb_detailed_quote_handle_submission() {
	if ( ! acb_detailed_quote_verify_nonce() ) {
		wp_send_json_error( array( 'message' => 'Security check failed. Please refresh the page and try again.' ) );
	}

	if ( function_exists( 'acb_spam_guard' ) ) {
		acb_spam_guard( 'detailed_quote' );
	}

	$full_name       = sanitize_text_field( wp_unslash( $_POST['full_name'] ?? '' ) );
	$company_name    = sanitize_text_field( wp_unslash( $_POST['company_name'] ?? '' ) );
	$email           = sanitize_email( wp_unslash( $_POST['email'] ?? '' ) );
	$phone           = sanitize_text_field( wp_unslash( $_POST['phone'] ?? '' ) );
	$country         = sanitize_text_field( wp_unslash( $_POST['country'] ?? '' ) );
	$box_style       = sanitize_text_field( wp_unslash( $_POST['box_style'] ?? '' ) );
	$length          = sanitize_text_field( wp_unslash( $_POST['length'] ?? '' ) );
	$width           = sanitize_text_field( wp_unslash( $_POST['width'] ?? '' ) );
	$height          = sanitize_text_field( wp_unslash( $_POST['height'] ?? '' ) );
	$quantity        = sanitize_text_field( wp_unslash( $_POST['quantity'] ?? '' ) );
	$material        = sanitize_text_field( wp_unslash( $_POST['material'] ?? '' ) );
	$thickness       = sanitize_text_field( wp_unslash( $_POST['thickness'] ?? '' ) );
	$printing        = sanitize_text_field( wp_unslash( $_POST['printing'] ?? '' ) );
	$finishing_other = sanitize_text_field( wp_unslash( $_POST['finishing_other'] ?? '' ) );
	$notes           = sanitize_textarea_field( wp_unslash( $_POST['notes'] ?? '' ) );

	$finishing_raw = wp_unslash( $_POST['finishing'] ?? array() );
	if ( ! is_array( $finishing_raw ) ) {
		$finishing_raw = array();
	}
	$finishing = implode( ', ', array_map( 'sanitize_text_field', $finishing_raw ) );

	if ( empty( $company_name ) ) {
		wp_send_json_error( array( 'message' => 'Please enter your company name.' ) );
	}

	if ( function_exists( 'acb_form_require_name_email_phone' ) ) {
		acb_form_require_name_email_phone( $full_name, $email, $phone );
	} elseif ( empty( $full_name ) || empty( $email ) || empty( $phone ) ) {
		wp_send_json_error( array( 'message' => 'Please fill in all required contact fields.' ) );
	} elseif ( ! is_email( $email ) ) {
		wp_send_json_error( array( 'message' => 'Please provide a valid email address.' ) );
	}

	$attachments = array();
	$tmp_files   = array();
	$file_labels = array();
	foreach ( array( 'logo_file' => 'Logo', 'artwork_file' => 'Artwork', 'reference_file' => 'Reference' ) as $field => $label ) {
		$result = acb_detailed_quote_save_upload( $field );
		if ( empty( $result['ok'] ) ) {
			foreach ( $tmp_files as $tmp ) {
				if ( file_exists( $tmp ) ) {
					wp_delete_file( $tmp );
				}
			}
			wp_send_json_error( array( 'message' => $result['error'] ?? 'Invalid upload.' ) );
		}
		if ( ! empty( $result['path'] ) ) {
			$attachments[] = $result['path'];
			$tmp_files[]   = $result['path'];
			$file_labels[] = $label . ': ' . basename( $result['path'] );
		}
	}

	$bodies = acb_detailed_quote_email_bodies(
		array(
			'full_name'       => $full_name,
			'company_name'    => $company_name,
			'email'           => $email,
			'phone'           => $phone,
			'country'         => $country,
			'box_style'       => $box_style,
			'length'          => $length,
			'width'           => $width,
			'height'          => $height,
			'quantity'        => $quantity,
			'material'        => $material,
			'thickness'       => $thickness,
			'printing'        => $printing,
			'finishing'       => $finishing,
			'finishing_other' => $finishing_other,
			'notes'           => $notes,
			'files_note'      => $file_labels ? implode( ' | ', $file_labels ) : 'No files uploaded',
		),
		true
	);

	$logo_url  = 'https://americacustomboxes.com/wp-content/uploads/2026/07/Acb-logo-landscape.webp';
	$logo_path = WP_CONTENT_DIR . '/uploads/2026/07/Acb-logo-landscape.webp';
	$tmp_logo  = null;

	$embed_logo = static function ( $phpmailer ) use ( $logo_path, $logo_url, &$tmp_logo ) {
		$embed_path = '';
		$embed_name = 'Acb-logo-landscape.png';

		// Prefer PNG for email clients (many reject WebP, including Gmail/Outlook).
		$source = file_exists( $logo_path ) ? $logo_path : '';
		if ( ! $source ) {
			$downloaded = download_url( $logo_url );
			if ( ! is_wp_error( $downloaded ) && file_exists( $downloaded ) ) {
				$tmp_logo = $downloaded;
				$source   = $downloaded;
			}
		}

		if ( $source && function_exists( 'imagecreatefromwebp' ) ) {
			$im = @imagecreatefromwebp( $source );
			if ( $im ) {
				$png = wp_tempnam( 'acb-logo.png' );
				if ( $png && @imagepng( $im, $png ) ) {
					$embed_path = $png;
					if ( $tmp_logo && $tmp_logo !== $png ) {
						@unlink( $tmp_logo );
					}
					$tmp_logo = $png;
				}
				imagedestroy( $im );
			}
		}

		if ( ! $embed_path && $source ) {
			$embed_path = $source;
			$embed_name = 'Acb-logo-landscape.webp';
		}

		if ( $embed_path && file_exists( $embed_path ) ) {
			$phpmailer->AddEmbeddedImage( $embed_path, 'acb_logo', $embed_name );
		}
	};
	add_action( 'phpmailer_init', $embed_logo, 10, 1 );

	$headers = array(
		'Content-Type: text/html; charset=UTF-8',
		'Reply-To: ' . $full_name . ' <' . $email . '>',
	);

	$GLOBALS['acb_detailed_quote_last_mail_error'] = null;
	$sent = wp_mail( 'sales@americacustomboxes.com', 'New Detailed Quote — ' . $full_name . ( $company_name ? ' (' . $company_name . ')' : '' ), $bodies['html'], $headers, $attachments );

	remove_action( 'phpmailer_init', $embed_logo, 10 );

	foreach ( $tmp_files as $tmp ) {
		if ( file_exists( $tmp ) ) {
			wp_delete_file( $tmp );
		}
	}
	if ( $tmp_logo && file_exists( $tmp_logo ) ) {
		@unlink( $tmp_logo );
	}

	if ( $sent ) {
		wp_send_json_success( array( 'message' => 'Thank you! Your detailed quote request has been sent.' ) );
	}
	wp_send_json_error( array( 'message' => 'Failed to send email. Please try again or email sales@americacustomboxes.com directly.' ) );
}
