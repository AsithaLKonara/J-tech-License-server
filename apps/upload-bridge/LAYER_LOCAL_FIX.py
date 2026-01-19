# LAYER-LOCAL FRAME GENERATION FIX
# Replace lines 9955-10043 in ui/tabs/design_tools_tab.py

# CRITICAL FIX: Layer-local frame generation (NOT global append)
# Layer 1: frames 0-11, Layer 2: frames 0-5 (NOT 12-17)
# Each layer maintains its own frame range independently

# Get active layer
tracks = self.layer_manager.get_layer_tracks()
active_idx = 0
if hasattr(self, 'layer_panel') and self.layer_panel:
    active_idx = self.layer_panel.get_active_layer_index()
    if active_idx < 0 or active_idx >= len(tracks):
        active_idx = 0

if not tracks:
    QMessageBox.warning(self, "No Layers", "No layers exist. Please create at least one layer.")
    return

active_track = tracks[active_idx]
width = self._pattern.metadata.width
height = self._pattern.metadata.height

# Create frames in the ACTIVE LAYER ONLY (layer-local indexing)
# Start from frame 0 (NOT from global frame count)
for frame_idx, new_frame in enumerate(unique_new_frames):
    # Apply transformations to this layer's frame
    source_layer_frame = active_track.get_frame(0) or active_track.get_or_create_frame(0, width, height)
    
    # Create new frame for this layer  
    layer_frame = source_layer_frame.copy()
    layer_frame.pixels = list(new_frame.pixels)
    
    # Store in layer track at LOCAL index (0, 1, 2, ..., N)
    active_track.set_frame(frame_idx, layer_frame)

# Set layer's frame boundaries (LAYER-LOCAL)
active_track.start_frame = 0
active_track.end_frame = len(unique_new_frames) - 1

# Update global pattern frame count to accommodate all layers
# Global frame count = max(all layer end_frames) + 1
max_frame_needed = 0
for track in tracks:
    if track.end_frame is not None:
        max_frame_needed = max(max_frame_needed, track.end_frame)

# Ensure global pattern has enough frames for all layers
required_global_frames = max_frame_needed + 1
current_global_frames = len(self._pattern.frames)

if required_global_frames > current_global_frames:
    # Add blank global frames (these are just placeholders for timeline)
    # Actual pixels come from layer rendering
    for _ in range(required_global_frames - current_global_frames):
        blank_frame = Frame(
            pixels=[(0, 0, 0)] *  (width * height),
            duration_ms=100
        )
        self._pattern.frames.append(blank_frame)

# Update UI
final_frame_count = len(self._pattern.frames)
self._log_frame_generation("COMPLETE", final_frame_count, {
    "frames_generated": len(new_frames),
    "unique_frames_added": len(unique_new_frames),
    "duplicates_filtered": duplicate_count,
    "initial_frames": initial_frame_count,
    "final_frames": final_frame_count,
    "layer_name": active_track.name,
    "layer_frame_range": f"0-{active_track.end_frame}",
    "layer_local": True  # Mark as layer-local generation
})

self.history_manager.set_frame_count(len(self._pattern.frames))
self.history_manager.set_current_frame(self._current_frame_index)
self.frame_manager.set_pattern(self._pattern)
self._load_current_frame_into_canvas()
self._refresh_timeline()
self._update_status_labels()
self._maybe_autosync_preview()
self.pattern_modified.emit()

# Show confirmation with layer-local info
QMessageBox.information(
    self,
    "Layer Animation Applied",
    f"Applied animation to layer '{active_track.name}'\\n"
    f"Layer frames: 0-{active_track.end_frame} ({len(unique_new_frames)} frames)\\n"
    f"Global timeline: {final_frame_count} frames\\n\\n"
    f"✓ Frame isolation: Each layer has its own frame range"
)
