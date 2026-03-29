# Quickstart: Standardized Flow Signaling & Routing

This guide provides a systematic workflow for verifying the standardized signaling and routing features.

## Setup Requirements
Ensure the following entities are available in the palette:
- `Factory`
- `Warehouse`
- `Guard`
- `Data Pipe`

## Verification Steps

### 1. Wildcard Routing ("any")
- Spawn a `Factory`.
- Spawn a `Data Pipe` and connect it as the source to a `Warehouse`.
- Set the `route_state` of the `Data Pipe` to `"any"`.
- Feed the `Factory` a payload.
- **SUCCESS**: The `Factory` processes and hands the payload into the `Data Pipe`, regardless of the `route_state` and without a routing table defined in the `Factory`.

### 2. Backpressure Signaling
- Setup: `Factory` -> `Data Pipe` -> `Warehouse`.
- Set the `capacity` of the `Data Pipe` to `1`.
- Set the `Warehouse` to `auto_release: false`.
- Feed 2 payloads to the `Factory`.
- **SUCCESS**: Once the `Warehouse` and `Data Pipe` are full, the `Factory` visual state turns **JAMMED** (Red) and stops processing.

### 3. Guard Optimization (Hibernation)
- Spawn a `Warehouse` and a `Guard`.
- Configure the `Guard` to monitor the `Warehouse`.
- Ensure the `Warehouse` is empty.
- **SUCCESS**: The `Guard`'s radar beam is **Blue** (IDLE) and rule-engine scan logs (if enabled) are not printed.
- Add a payload to the `Warehouse`.
- **SUCCESS**: The `Guard` beam briefly turns **Orange/Yellow** (Scanning) or **Green** (Pushed) to process the item.
