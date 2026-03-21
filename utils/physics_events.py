import constants

# --- Register Collision Types Dynamically if missing ---
if not hasattr(constants, 'COLLISION_TYPE_WAREHOUSE'):
    constants.COLLISION_TYPE_WAREHOUSE = 10
if not hasattr(constants, 'COLLISION_TYPE_PORTAL'):
    constants.COLLISION_TYPE_PORTAL = 11


class CollisionManager:
    """
    Centralized physics event mediator (M12).
    Manages Pymunk collision callbacks and routes them to logical entities.
    """

    def __init__(self, entities, active_instances, signal_queue):
        self.entities = entities
        self.active_instances = active_instances
        self.signal_queue = signal_queue

    def post_solve(self, arbiter, space, data):
        if arbiter.total_impulse.length > 200:
            shape_a, shape_b = arbiter.shapes
            for entity in self.entities:
                # Milestone 8: Improved collision detection for multifarious shapes
                if getattr(entity, 'shape', None) in (shape_a, shape_b) or \
                   any(s in (shape_a, shape_b) for s in getattr(entity, 'shapes', [])):
                    if hasattr(entity, 'handle_collision'):
                        entity.handle_collision(arbiter)

    def basket_sensor_begin(self, arbiter, space, data):
        basket_shape, projectile_shape = arbiter.shapes
        basket_entity = None
        projectile_entity = None

        for entity in self.entities:
            if getattr(entity, 'shape', None) == basket_shape or \
               basket_shape in getattr(entity, 'shapes', []):
                basket_entity = entity
            if getattr(entity, 'shape', None) == projectile_shape or \
               projectile_shape in getattr(entity, 'shapes', []):
                projectile_entity = entity

        if basket_entity and projectile_entity:
            if hasattr(basket_entity, 'collect_projectile'):
                basket_entity.collect_projectile(projectile_entity)
        return True

    def cannon_sensor_begin(self, arbiter, space, data):
        cannon_shape, projectile_shape = arbiter.shapes
        cannon_entity = None
        projectile_entity = None

        for entity in self.entities:
            if getattr(entity, 'shape', None) == cannon_shape or \
               cannon_shape in getattr(entity, 'shapes', []):
                cannon_entity = entity
            if getattr(entity, 'shape', None) == projectile_shape or \
               projectile_shape in getattr(entity, 'shapes', []):
                projectile_entity = entity

        if cannon_entity and projectile_entity:
            # Transfer logic
            if hasattr(cannon_entity, 'receive_signal'):
                cannon_entity.receive_signal(projectile_entity)
        return True

    def warehouse_sensor_begin(self, arbiter, space, data):
        """M30: Handles automated ingestion into Warehouse storage."""
        wh_shape, payload_shape = arbiter.shapes
        wh_entity = None
        payload_entity = None

        for entity in self.entities:
            if getattr(entity, 'shape', None) == wh_shape or \
               wh_shape in getattr(entity, 'shapes', []):
                wh_entity = entity
            if getattr(entity, 'shape', None) == payload_shape or \
               payload_shape in getattr(entity, 'shapes', []):
                payload_entity = entity

        if wh_entity and payload_entity and hasattr(wh_entity, "ingest_payload"):
            wh_entity.ingest_payload(payload_entity)
        return True

    def portal_sensor_begin(self, arbiter, space, data):
        """M30: Handles warp transit through Portal nodes."""
        portal_shape, payload_shape = arbiter.shapes
        portal_entity = None
        payload_entity = None

        for entity in self.entities:
            if getattr(entity, 'shape', None) == portal_shape or \
               portal_shape in getattr(entity, 'shapes', []):
                portal_entity = entity
            if getattr(entity, 'shape', None) == payload_shape or \
               payload_shape in getattr(entity, 'shapes', []):
                payload_entity = entity

        if portal_entity and payload_entity and hasattr(portal_entity, "warp_payload"):
            portal_entity.warp_payload(payload_entity, self.entities)
        return True

    def factory_sensor_pre_solve(self, arbiter, space, data):
        """M22: Handles ingestion into processing pipelines."""
        shape_a, shape_b = arbiter.shapes
        incoming_shape = shape_a if shape_b.collision_type == constants.COLLISION_TYPE_FACTORY_TOP else shape_b
        factory_shape = shape_b if shape_b.collision_type == constants.COLLISION_TYPE_FACTORY_TOP else shape_a
        
        incoming_entity = None
        factory_entity = None

        for entity in self.entities:
            if getattr(entity, 'shape', None) == incoming_shape or \
               incoming_shape in getattr(entity, 'shapes', []):
                incoming_entity = entity
            if getattr(entity, 'shape', None) == factory_shape or \
               factory_shape in getattr(entity, 'shapes', []):
                factory_entity = entity

        if factory_entity and incoming_entity and hasattr(factory_entity, "ingest_payload"):
            accepted = factory_entity.ingest_payload(incoming_entity)
            if accepted:
                return False  # Swallow ball
        return True

    def sink_sensor_pre_solve(self, arbiter, space, data):
        """M24: Standard ingestion into terminal DataSinks (using strict handshake)."""
        shape_a, shape_b = arbiter.shapes
        
        # Identify which shape is the sink sensor vs the incoming object
        incoming_shape = shape_a if shape_b.collision_type == constants.COLLISION_TYPE_SINK_TOP else shape_b
        sink_shape = shape_b if shape_b.collision_type == constants.COLLISION_TYPE_SINK_TOP else shape_a
        
        incoming_entity = None
        sink_entity = None

        # Resolve entities from shapes
        for entity in list(self.entities):
            if getattr(entity, 'shape', None) == incoming_shape or incoming_shape in getattr(entity, 'shapes', []):
                incoming_entity = entity
            if getattr(entity, 'shape', None) == sink_shape or sink_shape in getattr(entity, 'shapes', []):
                sink_entity = entity

        if not incoming_entity or not sink_entity:
            return True

        # Terminal ingestion handshake
        if hasattr(sink_entity, "ingest_payload"):
            # M32: Sinks utilize ingestion handshake and consumption backpressure
            accepted = sink_entity.ingest_payload(incoming_entity, self.active_instances)
            return not accepted # If accepted, return False to discard physical collision
            
        return True

    def setup(self, space):
        """Binds all collision handler callbacks to the provided Pymunk space."""
        # Note: space object here has a custom on_collision wrapper.
        space.on_collision(collision_type_a=None, collision_type_b=None, post_solve=self.post_solve)
        space.on_collision(collision_type_a=constants.COLLISION_TYPE_BASKET, collision_type_b=None, begin=self.basket_sensor_begin)
        space.on_collision(collision_type_a=constants.COLLISION_TYPE_CANNON, collision_type_b=None, begin=self.cannon_sensor_begin)
        space.on_collision(collision_type_a=constants.COLLISION_TYPE_FACTORY_TOP, collision_type_b=None, pre_solve=self.factory_sensor_pre_solve)
        space.on_collision(collision_type_a=constants.COLLISION_TYPE_SINK_TOP, collision_type_b=None, pre_solve=self.sink_sensor_pre_solve)
        space.on_collision(collision_type_a=constants.COLLISION_TYPE_WAREHOUSE, collision_type_b=None, begin=self.warehouse_sensor_begin)
        space.on_collision(collision_type_a=constants.COLLISION_TYPE_PORTAL, collision_type_b=None, begin=self.portal_sensor_begin)