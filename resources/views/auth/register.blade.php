@extends('layouts.auth')

@section('title', 'Register - Upload Bridge')

@section('content')
<form method="POST" action="{{ route('register') }}" class="auth-form">
    @csrf
    <div class="form-group">
        <label for="name">Name</label>
        <input type="text" id="name" name="name" value="{{ old('name') }}" required autofocus>
    </div>
    <div class="form-group">
        <label for="email">Email</label>
        <input type="email" id="email" name="email" value="{{ old('email') }}" required>
    </div>
    <div class="form-group">
        <label for="password">Password</label>
        <input type="password" id="password" name="password" required>
    </div>
    <div class="form-group">
        <label for="password_confirmation">Confirm Password</label>
        <input type="password" id="password_confirmation" name="password_confirmation" required>
    </div>
    <button type="submit" class="btn btn-primary btn-block">Register</button>
    <div class="auth-links">
        <a href="{{ route('login') }}">Already have an account? Login</a>
        <a href="{{ route('magic-link.request') }}">Login with magic link</a>
    </div>
</form>
@endsection

