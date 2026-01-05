@extends('layouts.app')

@section('title', 'Admin Dashboard')

@section('page-title', 'Admin Dashboard')

@section('content')
<div class="admin-section">
    <div class="dashboard-stats">
        <div class="stat-card">
            <h3>Total Users</h3>
            <p class="stat-value">{{ \App\Models\User::count() }}</p>
        </div>
        <div class="stat-card">
            <h3>Active Subscriptions</h3>
            <p class="stat-value">{{ \App\Models\Subscription::where('status', 'active')->count() }}</p>
        </div>
        <div class="stat-card">
            <h3>Total Licenses</h3>
            <p class="stat-value">{{ \App\Models\License::count() }}</p>
        </div>
        <div class="stat-card">
            <h3>Total Revenue</h3>
            <p class="stat-value">${{ number_format(\App\Models\Payment::where('status', 'completed')->sum('amount'), 2) }}</p>
        </div>
    </div>
    
    <div class="admin-links">
        <a href="{{ route('admin.users.index') }}" class="btn btn-primary">Manage Users</a>
        <a href="{{ route('admin.subscriptions.index') }}" class="btn btn-primary">Manage Subscriptions</a>
    </div>
</div>
@endsection

