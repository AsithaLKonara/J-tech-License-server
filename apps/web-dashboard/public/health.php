<?php
// Simple health check that doesn't require Laravel bootstrap
header('Content-Type: application/json');
http_response_code(200);
echo json_encode([
    'status' => 'ok',
    'service' => 'php-fpm',
    'timestamp' => date('c'),
]);
exit(0);
