<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>@yield('title', 'Upload Bridge')</title>
    <link rel="stylesheet" href="{{ asset('css/app.css') }}">
    @stack('styles')
</head>
<body class="dark-theme">
    @yield('content')
    <script src="{{ asset('js/app.js') }}"></script>
    @stack('scripts')
</body>
</html>
