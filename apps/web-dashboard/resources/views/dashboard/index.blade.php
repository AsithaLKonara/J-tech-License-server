@extends('layouts.app')

@section('title', 'Dashboard')

@section('page-title', 'Dashboard')

@section('content')
<div class="dashboard-stats">
    <div class="stat-card">
        <h3>Subscription Status</h3>
        <p class="stat-value">
            @if($subscription)
                <span class="badge badge-success">{{ ucfirst($subscription->plan_type) }}</span>
            @else
                <span class="badge badge-warning">No Active Subscription</span>
            @endif
        </p>
    </div>
    <div class="stat-card">
        <h3>License Status</h3>
        <p class="stat-value">
            @if($license)
                <span class="badge badge-success">Active</span>
            @else
                <span class="badge badge-error">Inactive</span>
            @endif
        </p>
    </div>
    <div class="stat-card">
        <h3>Devices</h3>
        <p class="stat-value">{{ $devices }}</p>
    </div>
    <div class="stat-card">
        <h3>Total Spent</h3>
        <p class="stat-value">${{ number_format($totalSpent, 2) }}</p>
    </div>
</div>

@if(!$subscription)
<div class="alert alert-warning">
    <p>You don't have an active subscription. <a href="{{ route('subscription') }}">Subscribe now</a> to unlock all features.</p>
</div>
@endif

@if($license)
<div class="license-info">
    <h2>Current License</h2>
    <div class="info-card">
        <p><strong>Plan:</strong> {{ ucfirst($license->plan) }}</p>
        <p><strong>Features:</strong> {{ implode(', ', (array) ($license->features ?? [])) }}</p>
        <p><strong>Expires:</strong> {{ $license->expires_at ? $license->expires_at->format('Y-m-d') : 'Never' }}</p>
    </div>
</div>
@endif
@endsection

