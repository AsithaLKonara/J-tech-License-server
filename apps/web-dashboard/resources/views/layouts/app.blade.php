<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>@yield('title', 'Upload Bridge Dashboard')</title>
    <link rel="stylesheet" href="{{ asset('css/app.css') }}?v={{ time() }}">
    @stack('styles')
</head>
<body class="dark-theme">
    <div class="dashboard-container">
        <aside class="sidebar">
            <div class="sidebar-header">
                <h2>Upload Bridge</h2>
            </div>
            <nav class="sidebar-nav">
                <a href="{{ route('dashboard') }}" class="nav-item {{ request()->routeIs('dashboard') ? 'active' : '' }}">
                    <span>Dashboard</span>
                </a>
                <a href="{{ route('subscription') }}" class="nav-item {{ request()->routeIs('subscription*') ? 'active' : '' }}">
                    <span>Subscription</span>
                </a>
                <a href="{{ route('licenses') }}" class="nav-item {{ request()->routeIs('licenses*') ? 'active' : '' }}">
                    <span>Licenses</span>
                </a>
                <a href="{{ route('devices') }}" class="nav-item {{ request()->routeIs('devices*') ? 'active' : '' }}">
                    <span>Devices</span>
                </a>
                <a href="{{ route('billing') }}" class="nav-item {{ request()->routeIs('billing*') ? 'active' : '' }}">
                    <span>Billing</span>
                </a>
                <a href="{{ route('account') }}" class="nav-item {{ request()->routeIs('account*') ? 'active' : '' }}">
                    <span>Account</span>
                </a>
                @auth
                    @if(auth()->user()->is_admin)
                        <a href="{{ route('admin.dashboard') }}" class="nav-item {{ request()->routeIs('admin.*') ? 'active' : '' }}">
                            <span>Admin</span>
                        </a>
                    @endif
                @endauth
            </nav>
        </aside>
        <main class="main-content">
            <header class="header">
                <div class="header-content">
                    <h1>@yield('page-title', 'Dashboard')</h1>
                    <div class="header-actions">
                        <span class="user-email">{{ auth()->user()->email }}</span>
                        <form method="POST" action="{{ route('logout') }}" class="inline">
                            @csrf
                            <button type="submit" class="btn btn-secondary">Logout</button>
                        </form>
                    </div>
                </div>
            </header>
            <div class="content-wrapper">
                @if(session('success'))
                    <div class="alert alert-success">{{ session('success') }}</div>
                @endif
                @if(session('error'))
                    <div class="alert alert-error">{{ session('error') }}</div>
                @endif
                @if($errors->any())
                    <div class="alert alert-error">
                        <ul>
                            @foreach($errors->all() as $error)
                                <li>{{ $error }}</li>
                            @endforeach
                        </ul>
                    </div>
                @endif
                @yield('content')
            </div>
        </main>
    </div>
    <script src="{{ asset('js/app.js') }}"></script>
    @stack('scripts')
</body>
</html>

