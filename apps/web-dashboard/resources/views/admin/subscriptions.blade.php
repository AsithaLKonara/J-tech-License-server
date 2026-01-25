@extends('layouts.app')

@section('title', 'Admin - Subscriptions')

@section('page-title', 'Subscription Management')

@section('content')
<div class="admin-section">
    <h2>All Subscriptions</h2>
    <table class="data-table">
        <thead>
            <tr>
                <th>ID</th>
                <th>User</th>
                <th>Plan</th>
                <th>Status</th>
                <th>Expires</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
            @foreach($subscriptions as $subscription)
            <tr>
                <td>{{ $subscription->id }}</td>
                <td>{{ $subscription->user->email }}</td>
                <td>{{ ucfirst($subscription->plan_type) }}</td>
                <td><span class="badge badge-{{ $subscription->status === 'active' ? 'success' : 'error' }}">{{ ucfirst($subscription->status) }}</span></td>
                <td>{{ $subscription->expires_at && is_object($subscription->expires_at) ? $subscription->expires_at->format('Y-m-d') : ($subscription->expires_at ?: 'Never') }}</td>
                <td>
                    <form method="POST" action="{{ route('admin.subscriptions.manual', $subscription->user_id) }}" class="inline-form">
                        @csrf
                        <select name="plan_type" required>
                            <option value="monthly">Monthly</option>
                            <option value="annual">Annual</option>
                            <option value="lifetime">Lifetime</option>
                        </select>
                        <button type="submit" class="btn btn-sm btn-primary">Create Manual</button>
                    </form>
                </td>
            </tr>
            @endforeach
        </tbody>
    </table>
    {{ $subscriptions->links() }}
</div>
@endsection

