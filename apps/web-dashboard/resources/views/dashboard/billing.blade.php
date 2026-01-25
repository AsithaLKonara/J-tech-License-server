@extends('layouts.app')

@section('title', 'Billing')

@section('page-title', 'Billing')

@section('content')
<div class="billing-section">
    <h2>Payment History</h2>
    @if($payments->isEmpty())
    <div class="alert alert-info">
        <p>No payment history yet.</p>
    </div>
    @else
    <table class="data-table">
        <thead>
            <tr>
                <th>Date</th>
                <th>Amount</th>
                <th>Status</th>
            </tr>
        </thead>
        <tbody>
            @foreach($payments as $payment)
            <tr>
                <td>{{ $payment->created_at->format('Y-m-d H:i') }}</td>
                <td>${{ number_format($payment->amount, 2) }} {{ strtoupper($payment->currency) }}</td>
                <td><span class="badge badge-{{ $payment->status === 'completed' ? 'success' : 'warning' }}">{{ ucfirst($payment->status) }}</span></td>
            </tr>
            @endforeach
        </tbody>
    </table>
    @endif
</div>
@endsection

