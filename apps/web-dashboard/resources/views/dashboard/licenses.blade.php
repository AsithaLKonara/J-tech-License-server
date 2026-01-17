@extends('layouts.app')

@section('title', 'Licenses')

@section('page-title', 'Licenses')

@section('content')
<div class="licenses-list">
    <h2>Your Licenses</h2>
    @if($licenses->isEmpty())
    <div class="alert alert-info">
        <p>You don't have any licenses yet. <a href="{{ route('subscription') }}">Subscribe</a> to get started.</p>
    </div>
    @else
    <table class="data-table">
        <thead>
            <tr>
                <th>Plan</th>
                <th>Features</th>
                <th>Status</th>
                <th>Expires</th>
                <th>Created</th>
            </tr>
        </thead>
        <tbody>
            @foreach($licenses as $license)
            <tr>
                <td>{{ ucfirst($license->plan) }}</td>
                <td>{{ implode(', ', (array) ($license->features ?? [])) }}</td>
                <td><span class="badge badge-{{ $license->status === 'active' ? 'success' : 'error' }}">{{ ucfirst($license->status) }}</span></td>
                <td>{{ $license->expires_at ? $license->expires_at->format('Y-m-d') : 'Never' }}</td>
                <td>{{ $license->created_at->format('Y-m-d') }}</td>
            </tr>
            @endforeach
        </tbody>
    </table>
    @endif
</div>
@endsection

