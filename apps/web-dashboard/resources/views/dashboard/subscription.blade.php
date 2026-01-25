@extends('layouts.app')

@section('title', 'Subscription')
@section('page-title', 'Subscription')

@section('content')

@php
    $hasActiveSubscription =
        $subscription &&
        in_array($subscription->status, ['active', 'pending']);

    $isLifetime =
        $subscription &&
        $subscription->plan_type === 'lifetime' &&
        $subscription->status === 'active';
@endphp

    {{-- Flash Messages --}}
    @if (session('success'))
        <div class="alert alert-success">
            {{ session('success') }}
        </div>
    @endif

    @if (session('error'))
        <div class="alert alert-danger">
            {{ session('error') }}
        </div>
    @endif

    {{-- Current Subscription --}}
    @if ($subscription)
        <div class="current-subscription mb-4">
            <h2>Current Subscription</h2>

            <div class="info-card">
                <p>
                    <strong>Plan:</strong>
                    {{ ucfirst($subscription->plan_type) }}
                </p>

                <p>
                    <strong>Status:</strong>
                    @php
                        $statusClass = match ($subscription->status) {
                            'active' => 'success',
                            'pending' => 'warning',
                            default => 'danger',
                        };
                    @endphp
                    <span class="badge badge-{{ $statusClass }}">
                        {{ ucfirst($subscription->status) }}
                    </span>
                </p>

                <p>
                    <strong>Expires:</strong>
                    {{ optional($subscription->expires_at)->format('Y-m-d') ?? 'Never' }}
                </p>

                @if ($subscription->status === 'active')
                    <form
                        method="POST"
                        action="{{ route('subscription.cancel') }}"
                        class="d-inline"
                        onsubmit="return confirm('Are you sure you want to cancel your subscription?')"
                    >
                        @csrf
                        <button type="submit" class="btn btn-danger">
                            Cancel Subscription
                        </button>
                    </form>
                @endif
            </div>
        </div>
    @endif

    {{-- Plans --}}
    <div class="plans-section">
        <h2>Choose a Plan</h2>

        <div class="pricing-grid">

            {{-- Monthly --}}
            <div class="pricing-card {{ $hasActiveSubscription ? 'disabled' : '' }}">
                @if ($subscription?->plan_type === 'monthly' && $subscription->status === 'active')
                    <span class="current-badge">Current Plan</span>
                @endif

                <h3>Monthly</h3>
                <div class="price">$9.99 <span>/month</span></div>
                <ul class="features-list">
                    <li>Pattern Upload</li>
                    <li>WiFi Upload</li>
                </ul>
                <button
                    type="button"
                    class="btn btn-primary btn-block"
                    {{ $hasActiveSubscription ? 'disabled' : '' }}
                    onclick="openPaymentModal('monthly')"
                >
                    Subscribe
                </button>
            </div>

            {{-- Annual --}}
            <div class="pricing-card featured {{ $hasActiveSubscription ? 'disabled' : '' }}">
                @if ($subscription?->plan_type === 'annual' && $subscription->status === 'active')
                    <span class="current-badge">Current Plan</span>
                @endif

                <h3>Annual</h3>
                <div class="price">$99.99 <span>/year</span></div>
                <ul class="features-list">
                    <li>Pattern Upload</li>
                    <li>WiFi Upload</li>
                    <li>Advanced Controls</li>
                </ul>
                <button
                    type="button"
                    class="btn btn-primary btn-block"
                    {{ $hasActiveSubscription ? 'disabled' : '' }}
                    onclick="openPaymentModal('annual')"
                >
                    Subscribe
                </button>
            </div>

            {{-- Lifetime --}}
            <div class="pricing-card {{ $hasActiveSubscription ? 'disabled' : '' }}">
                @if ($subscription?->plan_type === 'lifetime' && $subscription->status === 'active')
                    <span class="current-badge">Current Plan</span>
                @endif

                <h3>Lifetime</h3>
                <div class="price">$299.99 <span>one-time</span></div>
                <ul class="features-list">
                    <li>Pattern Upload</li>
                    <li>WiFi Upload</li>
                    <li>Advanced Controls</li>
                    <li>AI Features</li>
                </ul>
                <button
                    type="button"
                    class="btn btn-primary btn-block"
                    {{ $hasActiveSubscription ? 'disabled' : '' }}
                    onclick="openPaymentModal('lifetime')"
                >
                    Subscribe
                </button>
            </div>

        </div>
    </div>

@endsection

{{-- Payment Modal --}}
<div id="paymentModal" class="modal" role="dialog" aria-modal="true" aria-labelledby="paymentModalTitle">
    <div class="modal-content">

        <!-- Close Button -->
        <button
            type="button"
            class="close"
            aria-label="Close payment modal"
            onclick="closePaymentModal()"
        >
            &times;
        </button>

        <!-- Title -->
        <h2 id="paymentModalTitle">Choose Payment Method</h2>

        <p class="modal-subtitle">
            Select how you'd like to pay for your subscription
        </p>

        <!-- Payment Options -->
        <div class="payment-methods">

            <!-- Card -->
            <button
                type="button"
                class="payment-method-card"
                onclick="submitPayment('card')"
                aria-label="Pay with card"
            >
                <div class="payment-icon">💳</div>
                <h3>Card Payment</h3>
                <p>Pay securely with credit/debit card</p>
                <span class="payment-badge">Instant Activation</span>
            </button>

            <!-- Cash -->
            <button
                type="button"
                class="payment-method-card"
                onclick="submitPayment('cash')"
                aria-label="Pay with cash"
            >
                <div class="payment-icon">💵</div>
                <h3>Cash Payment</h3>
                <p>Pay with cash (admin approval required)</p>
                <span class="payment-badge">Manual Verification</span>
            </button>

        </div>
    </div>
</div>


{{-- Hidden Checkout Form --}}
<form
    id="subscriptionForm"
    method="POST"
    action="{{ route('subscription.checkout') }}"
>
    @csrf
    <input type="hidden" name="plan_type" id="planTypeInput">
    <input type="hidden" name="payment_method" id="paymentMethodInput">
</form>

{{-- Scripts --}}
<script>
    let selectedPlan = null;

    function openPaymentModal(planType) {
        selectedPlan = planType;
        document.getElementById('paymentModal').style.display = 'block';
        document.body.style.overflow = 'hidden';
    }

    function closePaymentModal() {
        document.getElementById('paymentModal').style.display = 'none';
        document.body.style.overflow = '';
    }

    function submitPayment(paymentMethod) {
        document.getElementById('planTypeInput').value = selectedPlan;
        document.getElementById('paymentMethodInput').value = paymentMethod;
        document.getElementById('subscriptionForm').submit();
    }

    document.addEventListener('click', function (event) {
        const modal = document.getElementById('paymentModal');
        if (event.target === modal) {
            closePaymentModal();
        }
    });
</script>
