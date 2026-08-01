<?php
/**
 * ACB Spam Protection — reCAPTCHA v3 + honeypot (layout-safe).
 * Deploy as Code Snippet: "ACB Spam Protection"
 *
 * Covers Instant Quote + Detailed Quote AJAX without editing page layouts.
 */
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

if ( ! defined( 'ACB_RECAPTCHA_SITE_KEY' ) ) {
	define( 'ACB_RECAPTCHA_SITE_KEY', '6LeGInAtAAAAAMCxJs8_6KOVGgwXMHDB65feVENh' );
}
if ( ! defined( 'ACB_RECAPTCHA_SECRET_KEY' ) ) {
	define( 'ACB_RECAPTCHA_SECRET_KEY', '6LeGInAtAAAAAGcsV79JYHBJ3gAU2JcVGswB08_2' );
}
if ( ! defined( 'ACB_RECAPTCHA_MIN_SCORE' ) ) {
	define( 'ACB_RECAPTCHA_MIN_SCORE', 0.5 );
}

/**
 * True when honeypot was filled (bot).
 */
function acb_spam_honeypot_tripped(): bool {
	$val = isset( $_POST['acb_hp_field'] ) ? trim( (string) wp_unslash( $_POST['acb_hp_field'] ) ) : '';
	return $val !== '';
}

/**
 * Verify Google reCAPTCHA v3 token.
 *
 * @return true|WP_Error
 */
function acb_spam_verify_recaptcha( string $token, string $expected_action ) {
	if ( $token === '' ) {
		return new WP_Error( 'acb_recaptcha_missing', 'Missing reCAPTCHA token.' );
	}

	$response = wp_remote_post(
		'https://www.google.com/recaptcha/api/siteverify',
		array(
			'timeout' => 12,
			'body'    => array(
				'secret'   => ACB_RECAPTCHA_SECRET_KEY,
				'response' => $token,
				'remoteip' => isset( $_SERVER['REMOTE_ADDR'] ) ? sanitize_text_field( wp_unslash( $_SERVER['REMOTE_ADDR'] ) ) : '',
			),
		)
	);

	if ( is_wp_error( $response ) ) {
		return $response;
	}

	$body = json_decode( (string) wp_remote_retrieve_body( $response ), true );
	if ( ! is_array( $body ) || empty( $body['success'] ) ) {
		return new WP_Error( 'acb_recaptcha_failed', 'reCAPTCHA verification failed.' );
	}

	$score  = isset( $body['score'] ) ? (float) $body['score'] : 0.0;
	$action = isset( $body['action'] ) ? (string) $body['action'] : '';

	if ( $expected_action && $action !== $expected_action ) {
		return new WP_Error( 'acb_recaptcha_action', 'reCAPTCHA action mismatch.' );
	}

	if ( $score < (float) ACB_RECAPTCHA_MIN_SCORE ) {
		return new WP_Error( 'acb_recaptcha_score', 'reCAPTCHA score too low.' );
	}

	return true;
}

/**
 * Require full name, email, and phone (server-side for all quote forms).
 */
function acb_form_require_name_email_phone( string $full_name, string $email, string $phone ): void {
	if ( trim( $full_name ) === '' || trim( $email ) === '' || trim( $phone ) === '' ) {
		wp_send_json_error(
			array(
				'message' => 'Please fill in your full name, email address, and phone number.',
			)
		);
	}
	if ( ! is_email( $email ) ) {
		wp_send_json_error(
			array(
				'message' => 'Please provide a valid email address.',
			)
		);
	}
}

/**
 * Save an uploaded image only (JPG/PNG/WEBP/GIF), max 5MB — shared by quote form handlers.
 *
 * @return array{ok:bool,path?:string,error?:string}
 */
function acb_form_save_image_upload( string $field ): array {
	if (
		! isset( $_FILES[ $field ] ) ||
		! is_array( $_FILES[ $field ] ) ||
		( $_FILES[ $field ]['error'] ?? UPLOAD_ERR_NO_FILE ) === UPLOAD_ERR_NO_FILE ||
		( $_FILES[ $field ]['size'] ?? 0 ) <= 0
	) {
		return array( 'ok' => true, 'path' => null );
	}

	$error = (int) ( $_FILES[ $field ]['error'] ?? UPLOAD_ERR_OK );
	if ( $error !== UPLOAD_ERR_OK ) {
		return array( 'ok' => false, 'error' => 'Upload failed. Please try again with an image under 5MB.' );
	}

	$max_bytes = 5 * 1024 * 1024;
	if ( (int) $_FILES[ $field ]['size'] > $max_bytes ) {
		return array( 'ok' => false, 'error' => 'Each image must be 5MB or smaller.' );
	}

	$tmp_path  = $_FILES[ $field ]['tmp_name'];
	$finfo     = function_exists( 'finfo_open' ) ? finfo_open( FILEINFO_MIME_TYPE ) : false;
	$file_type = $finfo ? finfo_file( $finfo, $tmp_path ) : ( function_exists( 'mime_content_type' ) ? ( mime_content_type( $tmp_path ) ?: '' ) : '' );
	if ( $finfo ) {
		finfo_close( $finfo );
	}

	$allowed = array( 'image/jpeg', 'image/png', 'image/webp', 'image/gif' );
	if ( ! in_array( $file_type, $allowed, true ) ) {
		return array( 'ok' => false, 'error' => 'Only image files are allowed (JPG, PNG, WEBP, GIF). PDF and other files are not accepted.' );
	}

	$image_info = @getimagesize( $tmp_path );
	if ( ! $image_info ) {
		return array( 'ok' => false, 'error' => 'Only valid image files are allowed.' );
	}

	$original_name = sanitize_file_name( wp_unslash( $_FILES[ $field ]['name'] ) );
	$ext           = strtolower( pathinfo( $original_name, PATHINFO_EXTENSION ) );
	$allowed_ext   = array( 'jpg', 'jpeg', 'png', 'webp', 'gif' );
	if ( ! in_array( $ext, $allowed_ext, true ) ) {
		return array( 'ok' => false, 'error' => 'Only image files are allowed (JPG, PNG, WEBP, GIF).' );
	}

	$upload_dir = wp_upload_dir();
	$dest_dir   = trailingslashit( $upload_dir['basedir'] ) . 'quote-uploads/';
	if ( ! file_exists( $dest_dir ) ) {
		wp_mkdir_p( $dest_dir );
	}
	$dest = $dest_dir . uniqid( 'dq_', true ) . '_' . $original_name;
	if ( ! move_uploaded_file( $tmp_path, $dest ) ) {
		return array( 'ok' => false, 'error' => 'Could not save uploaded image. Please try again.' );
	}
	return array( 'ok' => true, 'path' => $dest );
}

/**
 * Call at the start of AJAX form handlers.
 * Honeypot bots get a fake success (no email). Failed captcha gets a generic error.
 */
function acb_spam_guard( string $action ): void {
	if ( acb_spam_honeypot_tripped() ) {
		wp_send_json_success(
			array(
				'message' => 'Thank you! Your request has been sent. We will get back to you shortly.',
			)
		);
	}

	$token = isset( $_POST['g-recaptcha-response'] )
		? sanitize_text_field( wp_unslash( $_POST['g-recaptcha-response'] ) )
		: '';

	$result = acb_spam_verify_recaptcha( $token, $action );
	if ( is_wp_error( $result ) ) {
		wp_send_json_error(
			array(
				'message' => 'Security check failed. Please refresh the page and try again.',
			)
		);
	}
}

/**
 * Front-end: load v3 + inject honeypot + attach token to quote FormData fetches.
 * Does not change page layouts.
 */
add_action(
	'wp_enqueue_scripts',
	static function () {
		if ( is_admin() ) {
			return;
		}

		wp_enqueue_script(
			'google-recaptcha-v3',
			'https://www.google.com/recaptcha/api.js?render=' . rawurlencode( ACB_RECAPTCHA_SITE_KEY ),
			array(),
			null,
			true
		);

		$js = <<<'JS'
(function () {
  if (window.acbSpamProtectionInit) return;
  window.acbSpamProtectionInit = true;

  var SITE_KEY = window.acbRecaptchaSiteKey || '';
  var ACTIONS = {
    acb_submit_detailed_quote: 'detailed_quote',
    submit_quote_form: 'detailed_quote',
    acb_submit_instant_quote: 'instant_quote',
    submit_instant_quote: 'instant_quote'
  };

  var HP_CSS = '.acb-hp-wrap{position:absolute!important;left:-10000px!important;top:auto!important;width:1px!important;height:1px!important;overflow:hidden!important;opacity:0!important;pointer-events:none!important;z-index:-1!important;}';

  function ensureHpCss() {
    if (document.getElementById('acb-hp-css')) return;
    var s = document.createElement('style');
    s.id = 'acb-hp-css';
    s.textContent = HP_CSS;
    document.head.appendChild(s);
  }

  function injectHoneypot(form) {
    if (!form || form.querySelector('[name="acb_hp_field"]')) return;
    ensureHpCss();
    var wrap = document.createElement('div');
    wrap.className = 'acb-hp-wrap';
    wrap.setAttribute('aria-hidden', 'true');
    wrap.innerHTML = '<label>Leave this field empty<input type="text" name="acb_hp_field" value="" tabindex="-1" autocomplete="off"></label>';
    form.appendChild(wrap);
  }

  function scanForms(root) {
    var scope = root && root.querySelectorAll ? root : document;
    scope.querySelectorAll('#quoteForm, #acbQfForm, #acbQfFormArchive, form.acb-qf-form').forEach(injectHoneypot);
  }

  function ready(fn) {
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', fn);
    else fn();
  }

  ready(function () {
    scanForms(document);
    try {
      var mo = new MutationObserver(function (muts) {
        muts.forEach(function (m) {
          m.addedNodes && m.addedNodes.forEach(function (n) {
            if (n.nodeType !== 1) return;
            if (n.matches && (n.matches('#quoteForm, #acbQfForm, #acbQfFormArchive, form.acb-qf-form') || n.querySelector)) {
              scanForms(n);
            }
          });
        });
      });
      mo.observe(document.documentElement, { childList: true, subtree: true });
    } catch (e) {}
  });

  function attachHpFromDom(fd) {
    if (!(fd instanceof FormData) || fd.get('acb_hp_field') != null) return;
    var forms = document.querySelectorAll('#quoteForm, #acbQfForm, #acbQfFormArchive, form.acb-qf-form');
    for (var i = 0; i < forms.length; i++) {
      var hp = forms[i].querySelector('[name="acb_hp_field"]');
      if (hp) {
        fd.set('acb_hp_field', hp.value || '');
        return;
      }
    }
  }

  function getToken(actionName) {
    return new Promise(function (resolve, reject) {
      if (!SITE_KEY) {
        reject(new Error('Missing site key'));
        return;
      }
      if (typeof grecaptcha === 'undefined') {
        reject(new Error('reCAPTCHA not loaded'));
        return;
      }
      grecaptcha.ready(function () {
        grecaptcha.execute(SITE_KEY, { action: actionName }).then(resolve).catch(reject);
      });
    });
  }

  var origFetch = window.fetch;
  window.fetch = function (input, init) {
    init = init || {};
    var body = init.body;
    if (!(body instanceof FormData)) {
      return origFetch.apply(this, arguments);
    }
    var action = body.get('action');
    if (!action || !ACTIONS[action]) {
      return origFetch.apply(this, arguments);
    }

    attachHpFromDom(body);
    var recaptchaAction = ACTIONS[action];

    return getToken(recaptchaAction).then(function (token) {
      body.set('g-recaptcha-response', token);
      body.set('acb_recaptcha_action', recaptchaAction);
      return origFetch.call(window, input, init);
    }).catch(function () {
      // Still attempt request; server will reject without valid token.
      return origFetch.call(window, input, init);
    });
  };
})();
JS;

		wp_register_script( 'acb-spam-protection', false, array( 'google-recaptcha-v3' ), '1.0.0', true );
		wp_enqueue_script( 'acb-spam-protection' );
		wp_add_inline_script(
			'acb-spam-protection',
			'window.acbRecaptchaSiteKey=' . wp_json_encode( ACB_RECAPTCHA_SITE_KEY ) . ';' . $js,
			'before'
		);
	},
	20
);
