@extends('layouts.app')

@section('title', 'Subscription Success')

@section('page-title', 'Subscription Success')

@section('content')
<div class="success-message">
    <h2>Subscription Successful!</h2>
    <p>Your subscription has been activated. You can now access all features.</p>
    <a href="{{ route('dashboard') }}" class="btn btn-primary">Go to Dashboard</a>
</div>
@endsection

