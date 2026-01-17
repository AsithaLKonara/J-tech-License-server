@extends('layouts.app')

@section('title', 'Devices')

@section('page-title', 'Devices')

@section('content')
@if(!$license)
<div class="alert alert-warning">
    <p>You need an active license to manage devices. <a href="{{ route('subscription') }}">Subscribe now</a>.</p>
</div>
@else
<div class="devices-list">
    <h2>Registered Devices</h2>
    @if($devices->isEmpty())
    <div class="alert alert-info">
        <p>No devices registered yet.</p>
    </div>
    @else
    <table class="data-table">
        <thead>
            <tr>
                <th>Device ID</th>
                <th>Device Name</th>
                <th>Last Seen</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
            @foreach($devices as $device)
            <tr>
                <td>{{ $device->device_id }}</td>
                <td>{{ $device->device_name }}</td>
                <td>{{ $device->last_seen_at ? (\Illuminate\Support\Carbon::parse($device->last_seen_at))->format('Y-m-d H:i') : 'Never' }}</td>
                <td>
                    <form method="POST" action="{{ route('devices.destroy', $device->id) }}" class="inline-form">
                        @csrf
                        @method('DELETE')
                        <button type="submit" class="btn btn-danger btn-sm" onclick="return confirm('Remove this device?')">Remove</button>
                    </form>
                </td>
            </tr>
            @endforeach
        </tbody>
    </table>
    @endif
</div>
@endif
@endsection

