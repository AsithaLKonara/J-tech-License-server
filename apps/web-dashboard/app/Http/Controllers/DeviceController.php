<?php

namespace App\Http\Controllers;

use App\Models\Device;
use Illuminate\Http\Request;

class DeviceController extends Controller
{
    public function index()
    {
        $user = auth()->user();
        $entitlement = $user->activeEntitlement(); // Use entitlement for display info if needed
        
        // Fetch devices directly associated with the user
        $devices = $user->devices()->latest()->get();

        return view('dashboard.devices', [
            'devices' => $devices,
            'license' => $entitlement, // Pass entitlement as license for view compatibility
        ]);
    }

    public function destroy($id)
    {
        $device = Device::findOrFail($id);
        
        // Check ownership
        if ($device->license->user_id !== auth()->id()) {
            abort(403);
        }

        $device->delete();

        return back()->with('success', 'Device removed successfully.');
    }
}

