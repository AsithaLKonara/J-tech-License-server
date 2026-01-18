@extends('layouts.app')

@section('title', 'User Details - Admin')

@section('page-title', 'User Details')

@section('content')
<div class="admin-section">
    <div class="user-info">
        <h2>{{ $user->name }} ({{ $user->email }})</h2>
        <p><strong>ID:</strong> {{ $user->id }}</p>
        <p><strong>Admin:</strong> {{ $user->is_admin ? 'Yes' : 'No' }}</p>
        <p><strong>Created:</strong> {{ $user->created_at instanceof \DateTime || $user->created_at instanceof \Carbon\Carbon ? $user->created_at->format('Y-m-d H:i') : $user->created_at }}</p>
    </div>
    
    <div class="user-subscriptions">
        <h3>Subscriptions</h3>
        @if($user->subscriptions->isEmpty())
        <p>No subscriptions</p>
        @else
        <table class="data-table">
            <thead>
                <tr>
                    <th>Plan</th>
                    <th>Status</th>
                    <th>Expires</th>
                </tr>
            </thead>
            <tbody>
                @foreach($user->subscriptions as $subscription)
                <tr>
                    <td>{{ ucfirst($subscription->plan_type) }}</td>
                    <td><span class="badge badge-{{ $subscription->status === 'active' ? 'success' : 'error' }}">{{ ucfirst($subscription->status) }}</span></td>
                    <td>{{ $subscription->expires_at ? ($subscription->expires_at instanceof \DateTime || $subscription->expires_at instanceof \Carbon\Carbon ? $subscription->expires_at->format('Y-m-d') : $subscription->expires_at) : 'Never' }}</td>
                </tr>
                @endforeach
            </tbody>
        </table>
        @endif
    </div>
    
    <div class="user-licenses">
        <h3>Licenses</h3>
        @if($user->licenses->isEmpty())
        <p>No licenses</p>
        @else
        <table class="data-table">
            <thead>
                <tr>
                    <th>Plan</th>
                    <th>Features</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                @foreach($user->licenses as $license)
                <tr>
                    <td>{{ ucfirst($license->plan) }}</td>
                    <td>{{ implode(', ', (array) ($license->features ?? [])) }}</td>
                    <td><span class="badge badge-{{ $license->status === 'active' ? 'success' : 'error' }}">{{ ucfirst($license->status) }}</span></td>
                </tr>
                @endforeach
            </tbody>
        </table>
        @endif
    </div>
    
    <div class="admin-actions">
        <h3>Create Manual Subscription</h3>
        <form method="POST" action="{{ route('admin.subscriptions.manual', $user->id) }}" class="form">
            @csrf
            <div class="form-group">
                <label for="plan_type">Plan Type</label>
                <select name="plan_type" id="plan_type" required>
                    <option value="monthly">Monthly</option>
                    <option value="annual">Annual</option>
                    <option value="lifetime">Lifetime</option>
                </select>
            </div>
            <button type="submit" class="btn btn-primary">Create Subscription</button>
        </form>
    </div>
</div>
@endsection

