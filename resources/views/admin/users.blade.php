@extends('layouts.app')

@section('title', 'Admin - Users')

@section('page-title', 'User Management')

@section('content')
<div class="admin-section">
    <h2>All Users</h2>
    <table class="data-table">
        <thead>
            <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Email</th>
                <th>Subscriptions</th>
                <th>Licenses</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
            @foreach($users as $user)
            <tr>
                <td>{{ $user->id }}</td>
                <td>{{ $user->name }}</td>
                <td>{{ $user->email }}</td>
                <td>{{ $user->subscriptions->count() }}</td>
                <td>{{ $user->licenses->count() }}</td>
                <td>
                    <a href="{{ route('admin.users.show', $user) }}" class="btn btn-sm btn-primary">View</a>
                </td>
            </tr>
            @endforeach
        </tbody>
    </table>
    {{ $users->links() }}
</div>
@endsection

