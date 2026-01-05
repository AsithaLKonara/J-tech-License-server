@extends('layouts.auth')

@section('title', 'Login - Upload Bridge')

@section('content')
<form method="POST" action="{{ route('login') }}" class="auth-form">
    @csrf
    <div class="form-group">
        <label for="email">Email</label>
        <input type="email" id="email" name="email" value="{{ old('email') }}" required autofocus>
    </div>
    <div class="form-group">
        <label for="password">Password</label>
        <input type="password" id="password" name="password" required>
    </div>
    <div class="form-group">
        <label class="checkbox">
            <input type="checkbox" name="remember">
            <span>Remember me</span>
        </label>
    </div>
    <button type="submit" class="btn btn-primary btn-block">Login</button>
    <div class="auth-links">
        <a href="{{ route('register') }}">Don't have an account? Register</a>
        <a href="{{ route('magic-link.request') }}">Login with magic link</a>
    </div>
</form>
@endsection

