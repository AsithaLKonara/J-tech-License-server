@extends('layouts.landing')

@section('title', 'Upload Bridge - License Management')

@section('content')
<div class="landing-page">
    <section class="hero">
        <h1>Upload Bridge License Management</h1>
        <p class="hero-subtitle">Manage your licenses, subscriptions, and devices in one place</p>
        <div class="hero-actions">
            <a href="{{ route('register') }}" class="btn btn-primary btn-lg">Get Started</a>
            <a href="{{ route('login') }}" class="btn btn-secondary btn-lg">Login</a>
        </div>
    </section>

    <section class="features">
        <h2>Features</h2>
        <div class="features-grid">
            <div class="feature-card">
                <h3>Subscription Management</h3>
                <p>Monthly, annual, and lifetime plans with automatic renewal</p>
            </div>
            <div class="feature-card">
                <h3>License Control</h3>
                <p>Manage licenses and features for your account</p>
            </div>
            <div class="feature-card">
                <h3>Device Management</h3>
                <p>Track and manage devices using your licenses</p>
            </div>
            <div class="feature-card">
                <h3>Secure Payments</h3>
                <p>Stripe integration for secure payment processing</p>
            </div>
        </div>
    </section>

    <section class="pricing">
        <h2>Pricing Plans</h2>
        <div class="pricing-grid">
            <div class="pricing-card">
                <h3>Monthly</h3>
                <div class="price">$9.99<span>/month</span></div>
                <ul class="features-list">
                    <li>Pattern Upload</li>
                    <li>WiFi Upload</li>
                </ul>
                <a href="{{ route('register') }}" class="btn btn-primary">Get Started</a>
            </div>
            <div class="pricing-card featured">
                <h3>Annual</h3>
                <div class="price">$99.99<span>/year</span></div>
                <ul class="features-list">
                    <li>Pattern Upload</li>
                    <li>WiFi Upload</li>
                    <li>Advanced Controls</li>
                </ul>
                <a href="{{ route('register') }}" class="btn btn-primary">Get Started</a>
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
                <a href="{{ route('register') }}" class="btn btn-primary">Get Started</a>
            </div>
        </div>
    </section>
</div>
@endsection

