# Warehouse
**Category**: logic  
**Key Bind**: N/A

## Description
A logic component.

## Summary
Summary goes here.

## Detail
Detail goes here.

## Parameters and Functionality

### Baseline Properties
- `template`: Unknown
- `is_static`: True

### Additional Parameters
- `angle`: ``
- `auto_release`: `True`
- `capacity`: `20`
- `collision_sound`: `default_collision.wav`
- `elasticity`: `0.5`
- `friction`: `0.5`
- `height`: `96`
- `input_side`: `top`
- `mass`: `1.0`
- `output_side`: `bottom`
- `release_interval`: `1.0`
- `send_full_signal`: `True` (Standardised Flow signaling)
- `spawn_sound`: `spawn.wav`
- `velocity`: ``
- `width`: `96`

## Signaling & State
Warehouses participate in the standardized `FlowEntity` handshake.
- **ACTIVE**: Signal broadcast when the buffer contains at least one payload. Used to wake up connected **Guards**.
- **IDLE**: Signal broadcast when the buffer is empty.
- **FULL**: Signal broadcast when capacity is reached OR when the downstream path (e.g. Data Pipe) is JAMMED.

### Animation States
- `False`: `warehouse_off`
- `INITIALIZING`: `warehouse_initializing`
- `IDLE`: Empty buffer.
- `ACTIVE`: Payload present in buffer.
- `FULL`: Capacity reached or backpressure received.
- `INGESTING`: `warehouse_ingesting`
- `WRITING`: `warehouse_writing`
- `FATAL`: `warehouse_fatal`