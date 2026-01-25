@extends('layouts.app')

@section('title', 'Admin - Pending Payments')

@section('page-title', 'Pending Cash Payments')

@section('content')
@if(session('success'))
<div class="alert alert-success">{{ session('success') }}</div>
@endif

@if(session('error'))
<div class="alert alert-error">{{ session('error') }}</div>
@endif

<div class="admin-section">
    <h2>Pending Cash Payment Requests</h2>
    
    @if($payments->count() > 0)
    <table class="data-table">
        <thead>
            <tr>
                <th>ID</th>
                <th>User</th>
                <th>Plan Type</th>
                <th>Amount</th>
                <th>Requested</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
            @foreach($payments as $payment)
            <tr>
                <td>{{ $payment->id }}</td>
                <td>{{ $payment->user->email }}</td>
                <td>{{ ucfirst($payment->subscription->plan_type ?? 'N/A') }}</td>
                <td>${{ number_format($payment->amount, 2) }} {{ $payment->currency }}</td>
                <td>{{ $payment->created_at->format('Y-m-d H:i') }}</td>
                <td>
                    <div class="action-buttons">
                        <form method="POST" action="{{ route('admin.payments.approve', $payment->id) }}" class="inline-form">
                            @csrf
                            <input type="text" name="admin_notes" placeholder="Optional notes" class="small-input">
                            <button type="submit" class="btn btn-sm btn-success" onclick="return confirm('Approve this payment?')">Approve</button>
                        </form>
                        
                        <button type="button" class="btn btn-sm btn-danger" onclick="openRejectModal({{ $payment->id }})">Reject</button>
                    </div>
                </td>
            </tr>
            @endforeach
        </tbody>
    </table>
    {{ $payments->links() }}
    @else
    <p class="no-data">No pending cash payments at the moment.</p>
    @endif
</div>

<!-- Reject Modal -->
<div id="rejectModal" class="modal">
    <div class="modal-content">
        <span class="close" onclick="closeRejectModal()">&times;</span>
        <h2>Reject Payment</h2>
        <p>Please provide a reason for rejection:</p>
        
        <form id="rejectForm" method="POST">
            @csrf
            <textarea name="admin_notes" required placeholder="Reason for rejection..." rows="4" class="form-control"></textarea>
            <div class="modal-actions">
                <button type="button" class="btn btn-secondary" onclick="closeRejectModal()">Cancel</button>
                <button type="submit" class="btn btn-danger">Reject Payment</button>
            </div>
        </form>
    </div>
</div>

<script>
function openRejectModal(paymentId) {
    const modal = document.getElementById('rejectModal');
    const form = document.getElementById('rejectForm');
    form.action = '{{ url("admin/payments") }}/' + paymentId + '/reject';
    modal.style.display = 'block';
}

function closeRejectModal() {
    document.getElementById('rejectModal').style.display = 'none';
}

window.onclick = function(event) {
    const modal = document.getElementById('rejectModal');
    if (event.target == modal) {
        closeRejectModal();
    }
}
</script>
@endsection
