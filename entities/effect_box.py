import pygame
import pymunk
import os
from typing import Any, Dict, List, Optional
from entities.base import FlowEntity
from utils.visual_fx_manager import visual_fx_manager
from utils.sound_manager import sound_manager

class EffectBoxPart(FlowEntity):
    """
    Milestone 41: Visual Effect Emitter (Upgraded).
    Supports sequential triggering (daisy chaining) and a tiered state machine.
    """
    VALID_STATES = FlowEntity.VALID_STATES | {"DELAY", "FIRING", "COOLDOWN"}

    def __init__(self, space: pymunk.Space, x: float, y: float, variant_name: str = "effect_box"):
        super().__init__(space, x, y, variant_name)
        
        # Default Properties (from entities.yaml)
        self.properties.setdefault("effect_type", "confetti")
        self.properties.setdefault("daisy_chain", False)
        self.properties.setdefault("trigger_on_impact", False)
        self.properties.setdefault("delay_duration", 0.0)
        self.properties.setdefault("firing_duration", 1.0)
        self.properties.setdefault("cooldown_duration", 0.5)

        self.timer = 0.0
        self.trigger_timer = 0.0 # for auto-trigger
        
        # Visual/Logic state
        self.visual_state = "IDLE"

    def receive_signal(self, sender, signal_data: dict):
        """Standard signal handler to enter the trigger sequence."""
        super().receive_signal(sender, signal_data)
        
        # Only start trigger sequence if we are currently IDLE
        if self.visual_state == "IDLE":
            self._start_trigger_sequence()

    def _start_trigger_sequence(self):
        """Initializes the DELAY or FIRING phase."""
        delay = float(self.get_property("delay_duration", 0.0))
        if delay > 0.01:
            self._set_state("DELAY")
            self.timer = delay
        else:
            self._fire()

    def _fire(self):
        """Immediately enters FIRING state and spawns effect."""
        self._set_state("FIRING")
        self.timer = float(self.get_property("firing_duration", 1.0))
        
        # Spawn the actual visual payoff
        self._spawn_effect_payload()
        
        # Play Sound with Graceful Fallback
        effect_type = str(self.get_property("effect_type", "confetti")).lower()
        sound_file = f"{effect_type}.wav"
        try:
            sound_manager.play_sound(sound_file)
        except Exception:
            pass

    def _spawn_effect_payload(self):
        """Interacts with VisualFXManager to spawn particles."""
        effect_type = str(self.get_property("effect_type", "confetti")).lower()
        x, y = self.body.position.x, self.body.position.y
        
        if effect_type == "confetti":
            visual_fx_manager.spawn_confetti(x, y)
        elif effect_type == "firework":
            visual_fx_manager.spawn_firework(x, y)
        elif effect_type == "flare":
            visual_fx_manager.spawn_flare(x, y)
        elif effect_type == "glitter":
            visual_fx_manager.spawn_glitter(x, y)
        elif effect_type == "balloon":
            visual_fx_manager.spawn_balloon(x, y)
        elif effect_type == "fart":
            visual_fx_manager.spawn_fart(x, y)

    def _broadcast_daisy_chain(self, active_instances: Dict[str, Any]):
        """Signals downstream neighbors if daisy chain is enabled."""
        if self.get_bool_property("daisy_chain", False):
            signal = {
                "status": "EMITTING", # standard trigger signal
                "source_uuid": self.uuid,
                "event": "DAISY_CHAIN_TRIGGER"
            }
            # Milestone 41 Step 38 Fix: ensure broadcast uses current instances
            self.broadcast_status(active_instances, custom_signal=signal)

    def update_logic(self, dt: float, game_state: Dict[str, Any], entities: List[Any], active_instances: Optional[Dict[str, Any]] = None):
        if game_state.get("mode") != "PLAY":
            return

        super().update_logic(dt, game_state, entities, active_instances)

        # 1. Handle Auto-Trigger Timer (IDLE only)
        if self.visual_state == "IDLE":
            interval = float(self.get_property("auto_trigger_interval", 0.0))
            if interval > 0.1:
                self.trigger_timer += dt
                if self.trigger_timer >= interval:
                    self.trigger_timer = 0.0
                    self._start_trigger_sequence()

        # 2. Handle State Timer Transitions
        if self.timer > 0:
            self.timer -= dt
            if self.timer <= 0:
                if self.visual_state == "DELAY":
                    self._fire()
                elif self.visual_state == "FIRING":
                    # --- CASCADING HOOK: Broadcast at start or end of firing? ---
                    # The spec says "broadcast its own signal when it enters the FIRING state"
                    # But if we did it in _fire() we might lose access to active_instances 
                    # unless we pass it. We'll do it here if we want strict frame sync 
                    # or in _fire if we have instances. Re-check logic: 
                    # We'll broadcast at start of firing to allow "simultaneous" cascaded firing
                    # but with a slight frame-delay inherently from the broadcast queue.
                    self._set_state("COOLDOWN")
                    self.timer = float(self.get_property("cooldown_duration", 0.5))
                elif self.visual_state == "COOLDOWN":
                    self._set_state("IDLE")

        # Daisy chain broadcast check (start of FIRING)
        if self.visual_state == "FIRING" and self.timer > 0 and self.timer >= (float(self.get_property("firing_duration", 1.0)) - dt - 1e-5):
            # Only broadcast once at transition
            if active_instances:
                self._broadcast_daisy_chain(active_instances)

        # 3. Handle Continuous Effects (flare/glitter emit every frame during FIRING)
        if self.visual_state == "FIRING":
            effect_type = str(self.get_property("effect_type", "confetti")).lower()
            if effect_type in ["flare", "glitter"]:
                self._spawn_effect_payload()

        # 4. Impact Trigger Logic
        if self.visual_state == "IDLE" and self.get_bool_property("trigger_on_impact", False):
            # Query for contacts with dynamic bodies
            for shape in self.shapes:
                info = self.space.shape_query(shape)
                for i in info:
                    # Ignore overlaps with self or static space
                    if i.shape.body != self.body and i.shape.body != self.space.static_body:
                        self._start_trigger_sequence()
                        break

    def ingest_payload(self, payload_entity, active_instances=None, **kwargs):
        """Milestone 41: Trigger effect when a payload 'enters' the box."""
        if self.visual_state == "IDLE":
            self._start_trigger_sequence()
        # EffectBox doesn't 'keep' the ball
        payload_entity.to_delete = True
        return True
