@extends('layouts.app')

@section('title', 'Subscription')

@section('page-title', 'Subscription')

@section('content')
@if($subscription)
<div class="current-subscription">
    <h2>Current Subscription</h2>
    <div class="info-card">
        <p><strong>Plan:</strong> {{ ucfirst($subscription->plan_type) }}</p>
        <p><strong>Status:</strong> <span class="badge badge-{{ $subscription->status === 'active' ? 'success' : 'error' }}">{{ ucfirst($subscription->status) }}</span></p>
        <p><strong>Expires:</strong> {{ $subscription->expires_at ? $subscription->expires_at->format('Y-m-d') : 'Never' }}</p>
        @if($subscription->status === 'active')
        <form method="POST" action="{{ route('subscription.cancel') }}" class="inline-form">
            @csrf
            <button type="submit" class="btn btn-danger" onclick="return confirm('Are you sure you want to cancel your subscription?')">Cancel Subscription</button>
        </form>
        @endif
    </div>
</div>
@endif

<div class="plans-section">
    <h2>Choose a Plan</h2>
    <div class="pricing-grid">
        <div class="pricing-card">
            <h3>Monthly</h3>
            <div class="price">$9.99<span>/month</span></div>
            <ul class="features-list">
                <li>Pattern Upload</li>
                <li>WiFi Upload</li>
            </ul>
            <form method="POST" action="{{ route('subscription.checkout') }}">
                @csrf
                <input type="hidden" name="plan_type" value="monthly">
                <button type="submit" class="btn btn-primary btn-block">Subscribe</button>
            </form>
        </div>
        <div class="pricing-card featured">
            <h3>Annual</h3>
            <div class="price">$99.99<span>/year</span></div>
            <ul class="features-list">
                <li>Pattern Upload</li>
                <li>WiFi Upload</li>
                <li>Advanced Controls</li>
            </ul>
            <form method="POST" action="{{ route('subscription.checkout') }}">
                @csrf
                <input type="hidden" name="plan_type" value="annual">
                <button type="submit" class="btn btn-primary btn-block">Subscribe</button>
            </form>
        </div>
        <div class="pricing-card">
            <h3>Lifetime</h3>
            <div class="price">$299.99<span>one-time</span></div>
            <ul class="features-list">
                <li>Pattern Upload</li>
                <li>WiFi Upload</li>
                <li>Advanced Controls</li>
                <li>AI Features</li>
            </ul>
            <form method="POST" action="{{ route('subscription.checkout') }}">
                @csrf
                <input type="hidden" name="plan_type" value="lifetime">
                <button type="submit" class="btn btn-primary btn-block">Subscribe</button>
            </form>
        </div>
    </div>
</div>
@endsection

