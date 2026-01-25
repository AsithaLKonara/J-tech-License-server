@extends('layouts.app')

@section('title', 'Account Settings')

@section('page-title', 'Account Settings')

@section('content')
<div class="account-section">
    <div class="account-tabs">
        <button class="tab-btn active" data-tab="profile">Profile</button>
        <button class="tab-btn" data-tab="password">Password</button>
    </div>

    <div class="tab-content active" id="profile-tab">
        <h2>Profile Information</h2>
        <form method="POST" action="{{ route('account.update') }}" class="form">
            @csrf
            @method('PUT')
            <div class="form-group">
                <label for="name">Name</label>
                <input type="text" id="name" name="name" value="{{ auth()->user()->name }}" required>
            </div>
            <div class="form-group">
                <label for="email">Email</label>
                <input type="email" id="email" name="email" value="{{ auth()->user()->email }}" required>
            </div>
            <button type="submit" class="btn btn-primary">Update Profile</button>
        </form>
    </div>

    <div class="tab-content" id="password-tab">
        <h2>Change Password</h2>
        <form method="POST" action="{{ route('account.password') }}" class="form">
            @csrf
            @method('PUT')
            <div class="form-group">
                <label for="current_password">Current Password</label>
                <input type="password" id="current_password" name="current_password" required>
            </div>
            <div class="form-group">
                <label for="password">New Password</label>
                <input type="password" id="password" name="password" required>
            </div>
            <div class="form-group">
                <label for="password_confirmation">Confirm New Password</label>
                <input type="password" id="password_confirmation" name="password_confirmation" required>
            </div>
            <button type="submit" class="btn btn-primary">Update Password</button>
        </form>
    </div>
</div>
@endsection

@push('scripts')
<script>
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        btn.classList.add('active');
        document.getElementById(btn.dataset.tab + '-tab').classList.add('active');
    });
});
</script>
@endpush

