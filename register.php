<?php

header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');
header('X-Content-Type-Options: nosniff');

const REGISTRATION_RECIPIENT = 'wdd-egy@elmawy.com';
const MAX_REQUEST_BYTES = 16384;

function respond($status, $body)
{
    http_response_code($status);
    echo json_encode($body, JSON_UNESCAPED_UNICODE | JSON_INVALID_UTF8_SUBSTITUTE);
    exit;
}

function character_length($value)
{
    $count = preg_match_all('/./us', $value, $matches);
    return $count === false ? false : $count;
}

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    header('Allow: POST');
    respond(405, ['error' => 'Use the registration form to submit your details.']);
}

$requestBody = file_get_contents('php://input', false, null, 0, MAX_REQUEST_BYTES + 1);
if ($requestBody === false || strlen($requestBody) > MAX_REQUEST_BYTES) {
    respond(413, ['error' => 'The submission is too large. Please check the form and try again.']);
}

$contentType = strtolower(trim(explode(';', $_SERVER['CONTENT_TYPE'] ?? '')[0]));
if ($contentType === 'application/json') {
    try {
        $decoded = json_decode($requestBody, false, 512, JSON_THROW_ON_ERROR);
    } catch (JsonException $exception) {
        respond(400, ['error' => 'The submission could not be read. Please check the form and try again.']);
    }
    if (!is_object($decoded)) {
        respond(400, ['error' => 'Check the form fields and try again.']);
    }
    $payload = get_object_vars($decoded);
} elseif ($contentType === 'application/x-www-form-urlencoded') {
    $payload = $_POST;
} else {
    respond(415, ['error' => 'The registration form sent an unsupported request format.']);
}

if (!empty($payload['website'])) {
    respond(400, ['error' => 'Check the form fields and try again.']);
}

$fieldRules = [
    'fullName' => ['Full Name', 120],
    'specialty' => ['Medical Specialty', 120],
    'role' => ['Job Title', 120],
    'organization' => ['Hospital Organization', 160],
    'email' => ['Email address', 254],
    'phone' => ['Mobile Number', 40],
];
$errors = [];
$cleaned = [];

foreach ($fieldRules as $name => [$label, $maxLength]) {
    $value = $payload[$name] ?? '';
    if (!is_string($value)) {
        $value = '';
    }
    $value = trim($value);
    $length = character_length($value);

    if ($length === false) {
        $errors[$name] = "Enter valid text for {$label}.";
    } elseif ($length > $maxLength) {
        $errors[$name] = "{$label} must be {$maxLength} characters or fewer.";
    } elseif ($value === '') {
        $errors[$name] = 'Enter your ' . strtolower($label) . '.';
    } else {
        $cleaned[$name] = $value;
    }
}

if (isset($cleaned['email'])) {
    if (strlen($cleaned['email']) > 254 || filter_var($cleaned['email'], FILTER_VALIDATE_EMAIL) === false) {
        $errors['email'] = 'Enter a valid email address.';
    } else {
        $cleaned['email'] = strtolower($cleaned['email']);
    }
}

if (isset($cleaned['phone']) && strlen(preg_replace('/[^0-9]/', '', $cleaned['phone'])) < 7) {
    $errors['phone'] = 'Enter a phone number with at least 7 digits.';
}

$privacyAccepted = ($payload['privacyAccepted'] ?? null) === true
    || ($payload['privacyAccepted'] ?? null) === 'on'
    || ($payload['privacyAccepted'] ?? null) === '1';
if (!$privacyAccepted) {
    $errors['privacyAccepted'] = 'Please confirm the privacy notice to continue.';
}

if ($errors) {
    respond(422, [
        'error' => 'Please correct the highlighted fields.',
        'fields' => $errors,
    ]);
}

$messageLines = [
    'World Diabetes Day – Diabetes in Focus 2026 attendee registration',
    '',
    'Full Name: ' . $cleaned['fullName'],
    'Medical Specialty: ' . $cleaned['specialty'],
    'Job Title: ' . $cleaned['role'],
    'Hospital Organization: ' . $cleaned['organization'],
    'Email address: ' . $cleaned['email'],
    'Mobile Number: ' . $cleaned['phone'],
];
$subject = 'World Diabetes Day 2026 attendee registration';
$headers = "Content-Type: text/plain; charset=UTF-8\r\n";

try {
    $sent = mail(REGISTRATION_RECIPIENT, $subject, implode("\n", $messageLines), $headers);
} catch (Throwable $exception) {
    error_log('WDD registration mail handoff failed: ' . $exception->getMessage());
    respond(503, ['error' => 'We could not send your registration right now. Please try again later.']);
}

if (!$sent) {
    respond(503, ['error' => 'We could not send your registration right now. Please try again later.']);
}

respond(200, [
    'accepted' => true,
    'message' => 'Your registration has been submitted. The conference team will follow up using the contact details you provided.',
]);
