"""
M29: Smart Splitter Entity

Self-optimizing routing node using Ant Colony Optimization (ACO) principles.
Observes payload success/failure and dynamically adjusts routing weights
to favor the most successful path.
"""

import random
from typing import Dict, List, Any, Optional

import pygame
import pymunk

from entities.base import GamePart, FlowEntity
from utils.routing import calculate_ejection_kinematics
from utils.sprite_manager import sprite_manager


class SmartSplitterPart(FlowEntity):
    """
    A probabilistic payload router with adaptive learning.
    
    Routes payloads left or right based on calculated probabilities derived from
    accumulated success/failure feedback. Uses ACO-inspired weight adjustments to
    naturally optimize toward high-scoring paths without explicit user configuration.
    """

    def __init__(self, space: pymunk.Space, x: float, y: float, property_key: str = "smart_splitter"):
        super().__init__(space, x, y, property_key)
        
        # Initialize adaptive weights
        self.left_weight = float(self.get_property("left_weight", 10.0))
        self.right_weight = float(self.get_property("right_weight", 10.0))
        self.learning_rate = float(self.get_property("learning_rate", 2.0))
        
        # Defaults
        self.properties.setdefault("left_weight", 10.0)
        self.properties.setdefault("right_weight", 10.0)
        self.properties.setdefault("learning_rate", 2.0)
        self.properties.setdefault("width", 96.0)
        self.properties.setdefault("height", 96.0)
        
        # Make sensor to accept incoming payloads
        if self.shape:
            self.shape.sensor = True
        if self.body:
            self.body.body_type = pymunk.Body.KINEMATIC
        
        # Visual feedback
        self.flash_timer = 0.0
        self.last_choice = None  # Track last decision for visual feedback
        
        self._create_default_visuals()

    def _create_default_visuals(self):
        """Generate default splitter visual if no sprite available."""
        width = int(float(self.get_property("width", 96)))
        height = int(float(self.get_property("height", 96)))
        
        try:
            self.base_texture = sprite_manager.get_sprite(self.variant_key, width, height)
        except Exception:
            # Fallback: create simple dual-chute visual
            surf = pygame.Surface((width, height), pygame.SRCALPHA)
            pygame.draw.rect(surf, (100, 150, 255, 180), (0, 0, width, height))
            pygame.draw.rect(surf, (200, 200, 255), (0, 0, width, height), 3)
            
            # Draw left/right split indicator
            mid_x = width // 2
            pygame.draw.line(surf, (255, 255, 255), (mid_x, 0), (mid_x, height), 2)
            pygame.draw.polygon(surf, (100, 200, 100), [(0, height), (mid_x, height - 10), (mid_x, height)])
            pygame.draw.polygon(surf, (200, 100, 100), [(width, height), (mid_x, height - 10), (mid_x, height)])
            
            self.base_texture = surf

    def ingest_payload(self, payload_entity: GamePart, active_instances: Dict[str, Any] = None, skip_proximity: bool = False, **kwargs) -> bool:
        """
        Receive a payload and route it probabilistically.
        
        Records the routing decision in payload["trace"] for later feedback,
        then ejects the payload in the chosen direction.
        
        Args:
            payload_entity: The GamePart carrying the payload dict.
        
        Returns:
            bool: True if successfully ingested and routed.
        """
        # Hide the payload during transit
        payload_entity.is_hidden = True
        if getattr(payload_entity, "body", None):
            payload_entity.body.velocity = (0, 0)
            payload_entity.body.angular_velocity = 0
        
        # Initialize payload structure if needed
        if not hasattr(payload_entity, "payload") or not isinstance(payload_entity.payload, dict):
            payload_entity.payload = {}
        
        # Initialize trace if not present
        if "trace" not in payload_entity.payload:
            payload_entity.payload["trace"] = []
        
        # Calculate probability of routing left
        total_weight = self.left_weight + self.right_weight
        prob_left = self.left_weight / total_weight if total_weight > 0 else 0.5
        
        # Pick direction randomly based on probability
        chosen_dir = "left" if random.random() < prob_left else "right"
        self.last_choice = chosen_dir
        self.flash_timer = 15.0
        
        # Record decision in trace for feedback loop
        payload_entity.payload["trace"].append({
            "type": "splitter_decision",
            "uuid": self.uuid,
            "choice": chosen_dir
        })
        
        # Eject the payload in the chosen direction
        # Pass entities if available in kwargs, otherwise fallback to active_instances.values()
        entities = kwargs.get("entities", list(active_instances.values()) if active_instances else [])
        self._eject_payload(payload_entity, chosen_dir, entities, active_instances)
        
        return True

    def _eject_payload(self, payload_entity: GamePart, direction: str, entities: list, active_instances: dict):
        """
        M44: Eject a payload using standardized routing.
        Allows Data Pipes to be connected to specific outputs (Left=10, Right=20).
        """
        # Determine numeric state for pipe matching
        route_state = 10.0 if direction == "left" else 20.0

        # Determine if we should match by generic type if the payload has one
        payload_type = None
        if hasattr(payload_entity, "payload") and isinstance(payload_entity.payload, dict):
            payload_type = payload_entity.payload.get("type")

        # Use unified router
        result = self.resolve_exit_path(
            payload_entity, 
            route_state, 
            entities, 
            active_instances,
            override_side=direction,
            data_type=payload_type
        )

        if result == "pipe":
            # Handled by pipe visuals
            pass
        elif result == "jammed":
            # Splitter doesn't have a buffer, so if a pipe is jammed, we fallback to physical 
            # (or we could implement a small buffer, but for now we fallback to physical ejection)
            # Actually, standard behavior for unbuffered is to force through or drop.
            # We'll re-call without the pipe check if jammed? Or just let it hard-eject.
            pass

    def receive_signal(self, sender, signal_data: Dict[str, Any]):
        """
        Receive feedback signal from a DataSink about payload outcome.
        
        When a DataSink successfully processes a payload that passed through
        this splitter, it sends back feedback including:
        - "feedback": "SUCCESS" | "FAILURE"
        - "choice": "left" | "right"
        - "score": final_score (float)
        
        This method updates the routing weights based on the outcome.
        
        Args:
            sender: The entity sending the signal.
            signal_data: Dict with feedback, choice, and optional score.
        """
        if not isinstance(signal_data, dict):
            return
        
        feedback = signal_data.get("feedback", "").upper()
        choice = signal_data.get("choice", "").lower()
        score = signal_data.get("score", 0.0)
        
        if choice not in ["left", "right"]:
            return
        
        # Increase weight of successful path
        if feedback == "SUCCESS":
            if choice == "left":
                self.left_weight += self.learning_rate
            else:
                self.right_weight += self.learning_rate
        
        # Decrease weight of failed path (or increase opposite path)
        elif feedback == "FAILURE":
            if choice == "left":
                # Slightly increase right instead of heavily penalizing left
                self.right_weight += self.learning_rate * 0.5
            else:
                self.left_weight += self.learning_rate * 0.5
        
        # Normalize to prevent overflow (optional, but keeps weights reasonable)
        total = self.left_weight + self.right_weight
        if total > 1000.0:
            scale = 100.0 / total
            self.left_weight *= scale
            self.right_weight *= scale
        
        # Update properties for persistence (save/load)
        self.properties["left_weight"] = self.left_weight
        self.properties["right_weight"] = self.right_weight

    def update_logic(self, dt: float, game_state: Dict[str, Any], entities: List[GamePart], active_instances=None):
        """
        Update splitter state (cooldown effects, etc.).
        
        Args:
            dt: Delta time in seconds.
            game_state: Global game state dict.
            entities: World entity list.
            active_instances: UUID -> entity map.
        """
        super().update_logic(dt, game_state, entities, active_instances)
        
        if self.flash_timer > 0:
            self.flash_timer -= dt

    def draw(self, surface: pygame.Surface, camera=None):
        """
        Draw the splitter with visual probability indicator.
        
        Shows a bar above the splitter indicating the left/right weight ratio:
        - Green represents left probability
        - Red represents right probability
        
        Args:
            surface: Pygame surface to draw on.
            camera: Optional camera for coordinate transformation.
        """
        # Draw base entity texture
        super().draw(surface, camera)
        
        if not self.body:
            return
        
        # Calculate screen position
        if camera:
            screen_x, screen_y = camera.world_to_screen(self.body.position.x, self.body.position.y)
        else:
            screen_x, screen_y = self.body.position.x, self.body.position.y
        
        # Draw probability indicator bar
        width = int(float(self.get_property("width", 96)))
        height = int(float(self.get_property("height", 96)))
        
        bar_width = width - 8
        bar_height = 4
        bar_y = screen_y - height // 2 - 15
        bar_x = screen_x - bar_width // 2
        
        # Calculate probabilities
        total_weight = self.left_weight + self.right_weight
        prob_left = (self.left_weight / total_weight) if total_weight > 0 else 0.5
        prob_right = 1.0 - prob_left
        
        # Draw left (green) and right (red) portions of the bar
        left_px = int(bar_width * prob_left)
        
        # Flash effect if recently made a decision
        flash_intensity = max(0, self.flash_timer / 15.0)
        
        # Left bar (green)
        left_color = (
            int(100 + 155 * flash_intensity) if self.last_choice == "left" else 100,
            int(200 + 55 * flash_intensity),
            100
        )
        pygame.draw.rect(surface, left_color, (int(bar_x), int(bar_y), left_px, bar_height))
        
        # Right bar (red)
        right_color = (
            int(200 + 55 * flash_intensity),
            100,
            int(100 + 155 * flash_intensity) if self.last_choice == "right" else 100
        )
        pygame.draw.rect(
            surface,
            right_color,
            (int(bar_x + left_px), int(bar_y), bar_width - left_px, bar_height)
        )
        
        # Border
        pygame.draw.rect(surface, (255, 255, 255), (int(bar_x), int(bar_y), bar_width, bar_height), 1)
        
        # Draw text labels (L and R)
        try:
            font = pygame.font.SysFont(None, 18)
            
            left_text = font.render("L", True, (255, 255, 255))
            surface.blit(left_text, (int(bar_x + 2), int(bar_y - 12)))
            
            right_text = font.render("R", True, (255, 255, 255))
            surface.blit(right_text, (int(bar_x + bar_width - 8), int(bar_y - 12)))
            
            # Probability percentages
            perc_text = font.render(f"{prob_left*100:.0f}%", True, (200, 200, 200))
            surface.blit(perc_text, (int(screen_x - 20), int(bar_y - 12)))
        except Exception:
            pass  # Silent fail on font rendering issues
