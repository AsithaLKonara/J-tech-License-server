<?php

namespace App\Http\Controllers;

use App\Models\Device;
use Illuminate\Http\Request;

class DeviceController extends Controller
{
    public function index()
    {
        $user = auth()->user();
        $license = $user->activeLicense();
        
        $devices = $license ? $license->devices()->latest()->get() : collect();
        
        // Fix: Get devices through user's licenses
        if (!$license) {
            $devices = Device::whereHas('license', function($query) use ($user) {
                $query->where('user_id', $user->id);
            })->latest()->get();
        }

        return view('dashboard.devices', [
            'devices' => $devices,
            'license' => $license,
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

