import constants

# --- Register Collision Types Dynamically if missing ---
if not hasattr(constants, 'COLLISION_TYPE_WAREHOUSE'):
    constants.COLLISION_TYPE_WAREHOUSE = 10
if not hasattr(constants, 'COLLISION_TYPE_PORTAL'):
    constants.COLLISION_TYPE_PORTAL = 11


class CollisionManager:
    """
    Handles all physics collision callbacks to decouple Pymunk logic from the main Pygame loop.
    Maintains active references to the game's core entity and signal lists.
    """
    def __init__(self, entities, active_instances, signal_queue):
        self.entities = entities
        self.active_instances = active_instances
        self.signal_queue = signal_queue

    def post_solve(self, arbiter, space, data):
        if arbiter.total_impulse.length > 200:
            shape_a, shape_b = arbiter.shapes
            for entity in self.entities:
                if getattr(entity, 'shape', None) in (shape_a, shape_b) or \
                   (hasattr(entity, 'shapes') and (shape_a in entity.shapes or shape_b in entity.shapes)):
                    entity.play_event_sound("collision_sound")
        return True

    def basket_sensor_begin(self, arbiter, space, data):
        shape_a, shape_b = arbiter.shapes
        target_shape = shape_a if shape_b.collision_type == constants.COLLISION_TYPE_BASKET else shape_b
        basket_shape = shape_b if shape_b.collision_type == constants.COLLISION_TYPE_BASKET else shape_a
        
        target_entity = None
        basket_entity = None
        
        for entity in list(self.entities):
            if getattr(entity, 'shape', None) == target_shape or target_shape in getattr(entity, 'shapes', []):
                target_entity = entity
            if getattr(entity, 'shape', None) == basket_shape or basket_shape in getattr(entity, 'shapes', []):
                basket_entity = entity
                    
        if target_entity and basket_entity:
            accepts = basket_entity.get_property("accepts_types", ["all"])
            if isinstance(accepts, str):
                accepts = [accepts]
                
            if "all" in accepts or target_entity.variant_key in accepts:
                target_entity.to_delete = True
                if basket_entity not in self.signal_queue:
                    self.signal_queue.append(basket_entity)
                return False
            else:
                return True
        return False

    def cannon_sensor_begin(self, arbiter, space, data):
        shape_a, shape_b = arbiter.shapes
        target_shape = shape_a if shape_b.collision_type == constants.COLLISION_TYPE_CANNON else shape_b
        cannon_shape = shape_b if shape_b.collision_type == constants.COLLISION_TYPE_CANNON else shape_a
        
        for entity in list(self.entities):
            if getattr(entity, 'shape', None) == target_shape or target_shape in getattr(entity, 'shapes', []):
                entity.to_delete = True
                break
                
        for entity in list(self.entities):
            if getattr(entity, 'shape', None) == cannon_shape or cannon_shape in getattr(entity, 'shapes', []):
                entity.force_shoot = True
                if entity not in self.signal_queue:
                    self.signal_queue.append(entity)
                break
                
        return False

    def factory_sensor_pre_solve(self, arbiter, space, data):
        shape_a, shape_b = arbiter.shapes
        incoming_shape = shape_a if shape_b.collision_type == constants.COLLISION_TYPE_FACTORY_TOP else shape_b
        factory_shape = shape_b if shape_b.collision_type == constants.COLLISION_TYPE_FACTORY_TOP else shape_a

        incoming_entity = None
        factory_entity = None

        for entity in list(self.entities):
            if getattr(entity, 'shape', None) == incoming_shape or incoming_shape in getattr(entity, 'shapes', []):
                incoming_entity = entity
            if getattr(entity, 'shape', None) == factory_shape or factory_shape in getattr(entity, 'shapes', []):
                factory_entity = entity

        if not incoming_entity or not factory_entity:
            return True

        if getattr(factory_entity, 'variant_key', None) not in ('logic_factory', 'ai_brain'):
            return True

        if incoming_entity.uuid == factory_entity.uuid:
            return True

        if getattr(factory_entity, 'current_payload_uuid', None) == incoming_entity.uuid:
            return False

        if getattr(factory_entity, 'cooldown_timer', 0.0) > 0.0:
            return True

        accepted = factory_entity.ingest_payload(incoming_entity)
        if accepted:
            return False 
            
        return True 

    def warehouse_sensor_pre_solve(self, arbiter, space, data):
        shape_a, shape_b = arbiter.shapes
        incoming_shape = shape_a if shape_b.collision_type == constants.COLLISION_TYPE_WAREHOUSE else shape_b
        warehouse_shape = shape_b if shape_b.collision_type == constants.COLLISION_TYPE_WAREHOUSE else shape_a

        incoming_entity = None
        warehouse_entity = None

        for entity in list(self.entities):
            if getattr(entity, 'shape', None) == incoming_shape or incoming_shape in getattr(entity, 'shapes', []):
                incoming_entity = entity
            if getattr(entity, 'shape', None) == warehouse_shape or warehouse_shape in getattr(entity, 'shapes', []):
                warehouse_entity = entity

        if not incoming_entity or not warehouse_entity:
            return True

        if getattr(warehouse_entity, 'variant_key', None) != 'warehouse' and not getattr(warehouse_entity, 'variant_key', '').startswith('warehouse'):
            return True

        if incoming_entity.uuid == warehouse_entity.uuid:
            return True

        if incoming_entity.uuid in getattr(warehouse_entity, 'stored_payload_uuids', []):
            return False

        accepted = warehouse_entity.ingest_payload(incoming_entity)
        if accepted:
            return False 
        return True

    def portal_sensor_pre_solve(self, arbiter, space, data):
        shape_a, shape_b = arbiter.shapes
        incoming_shape = shape_a if shape_b.collision_type == constants.COLLISION_TYPE_PORTAL else shape_b
        portal_shape = shape_b if shape_b.collision_type == constants.COLLISION_TYPE_PORTAL else shape_a

        incoming_entity = None
        portal_entity = None

        for entity in list(self.entities):
            if getattr(entity, 'shape', None) == incoming_shape or incoming_shape in getattr(entity, 'shapes', []):
                incoming_entity = entity
            if getattr(entity, 'shape', None) == portal_shape or portal_shape in getattr(entity, 'shapes', []):
                portal_entity = entity

        if not incoming_entity or not portal_entity:
            return True

        if getattr(portal_entity, 'variant_key', None) != 'portal' and not getattr(portal_entity, 'variant_key', '').startswith('portal'):
            return True

        if incoming_entity.uuid == portal_entity.uuid:
            return True

        for item in getattr(portal_entity, 'transit_queue', []):
            if item.get("payload_uuid") == incoming_entity.uuid:
                return False

        accepted = portal_entity.ingest_payload(incoming_entity, self.entities)
        if accepted:
            return False 
        return True

    def sink_sensor_pre_solve(self, arbiter, space, data):
        shape_a, shape_b = arbiter.shapes
        incoming_shape = shape_a if shape_b.collision_type == constants.COLLISION_TYPE_SINK_TOP else shape_b
        sink_shape = shape_b if shape_b.collision_type == constants.COLLISION_TYPE_SINK_TOP else shape_a

        incoming_entity = None
        sink_entity = None

        for entity in list(self.entities):
            if getattr(entity, 'shape', None) == incoming_shape or incoming_shape in getattr(entity, 'shapes', []):
                incoming_entity = entity
            if getattr(entity, 'shape', None) == sink_shape or sink_shape in getattr(entity, 'shapes', []):
                sink_entity = entity

        if not incoming_entity or not sink_entity:
            return True

        if getattr(sink_entity, 'variant_key', '').startswith('data_sink') is False:
            return True

        if incoming_entity.uuid == sink_entity.uuid:
            return True

        accepted = sink_entity.ingest_payload(incoming_entity, self.active_instances)
        return not accepted

    def setup(self, space):
        """Binds all collision handler callbacks to the provided Pymunk space."""
        space.on_collision(collision_type_a=None, collision_type_b=None, post_solve=self.post_solve)
        space.on_collision(collision_type_a=constants.COLLISION_TYPE_BASKET, collision_type_b=None, begin=self.basket_sensor_begin)
        space.on_collision(collision_type_a=constants.COLLISION_TYPE_CANNON, collision_type_b=None, begin=self.cannon_sensor_begin)
        
        space.on_collision(
            collision_type_a=constants.COLLISION_TYPE_FACTORY_TOP,
            collision_type_b=None,
            pre_solve=self.factory_sensor_pre_solve,
        )
        space.on_collision(
            collision_type_a=constants.COLLISION_TYPE_WAREHOUSE,
            collision_type_b=None,
            pre_solve=self.warehouse_sensor_pre_solve,
        )
        space.on_collision(
            collision_type_a=constants.COLLISION_TYPE_PORTAL,
            collision_type_b=None,
            pre_solve=self.portal_sensor_pre_solve,
        )
        space.on_collision(
            collision_type_a=constants.COLLISION_TYPE_SINK_TOP,
            collision_type_b=None,
            pre_solve=self.sink_sensor_pre_solve,
        )