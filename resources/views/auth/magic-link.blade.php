@extends('layouts.auth')

@section('title', 'Magic Link Login - Upload Bridge')

@section('content')
<form method="POST" action="{{ route('magic-link.request') }}" class="auth-form">
    @csrf
    <div class="form-group">
        <label for="email">Email</label>
        <input type="email" id="email" name="email" value="{{ old('email') }}" required autofocus>
        <small>We'll send you a magic link to login without a password</small>
    </div>
    <button type="submit" class="btn btn-primary btn-block">Send Magic Link</button>
    <div class="auth-links">
        <a href="{{ route('login') }}">Back to login</a>
        <a href="{{ route('register') }}">Create account</a>
    </div>
</form>
@endsection

