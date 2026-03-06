Role: Lead System Designer

Context: Please read docs/CONSTITUTION.md and our current docs/SPECIFICATION.md. We are ready to define the next feature for our game: an Adjustable Angled Ramp.

Task: Generate an updated specification (or an addendum) for this new feature.

Feature Requirements:

Interaction (Edit Mode): The user must be able to spawn a ramp and specifically adjust its angle/rotation using the mouse or keyboard controls while in Edit Mode.

Physics (Play Mode): The ramp must be a static physics body. When a dynamic ball falls onto it, normal gravity-based behavior must occur—the ball should roll down the incline, driven by the physics engine's gravity, friction, and moment of inertia calculations.

Mandatory Quality Assurance: > Per Section 6 of our Constitution, you MUST include a new step-by-step "Manual Test Script & Success Criteria" specifically for this feature. The human test must include steps to:

Spawn the adjustable ramp.

Change its angle.

Position a ball above it.

Enter Play Mode and verify that the ball actively rolls down the incline (rather than just bouncing or sliding statically).

Please output the updated specification requirements for my approval before we move to the implementation plan.