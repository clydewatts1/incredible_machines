Visual Effects Reference (Milestone 41)

The EffectBoxPart supports multiple visual payloads. You can configure which effect plays by changing the effect_type property in the UI Inspector or entities.yaml.

Available Effect Types

1. confetti (Default)

Visual: An instant explosion of multicolored, spinning rectangular particles.

Behavior: Particles shoot upwards and outwards in a cone, then slowly drift downwards under the influence of gravity.

Best For: Goal completions, scoring high points.

2. firework

Visual: A single bright "rocket" shoots straight up into the air.

Behavior: After reaching its apex (or after a set time), the rocket vanishes and spawns a perfect 360-degree radial burst of bright, glowing particles.

Best For: End-of-level celebrations, chaining multiple boxes together for a finale.

3. flare

Visual: A continuous, intense fountain of bright orange and red sparks.

Behavior: Rapidly emits short-lived glowing particles upwards while the effect is in the FIRING state. Uses additive blending to create a "glowing" core.

Best For: Warning signals, indicating a machine is JAMMED or a queue is full.

4. glitter

Visual: A continuous spray of tiny, shiny golden and white squares.

Behavior: Shoots in a wide arc, floating gently downwards with high air resistance (slow fall).

Best For: Subtle, magical celebrations for rare item routing.

5. balloon

Visual: Spawns a few large, colorful circles with a small "string" line attached.

Behavior: Drifts slowly upwards, swaying left and right. Pops (vanishes instantly) when the duration ends.

Best For: Playful, non-intrusive background movement.

Audio Fallbacks

Every effect attempts to play a sound file located in assets/sounds/[effect_type].wav (e.g., assets/sounds/firework.wav). If the file is missing, the game gracefully ignores the audio and only plays the visual effect, preventing crashes.