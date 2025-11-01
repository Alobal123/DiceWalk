from core.event_listener import EventListener
from core.game_event import GameEvent, GameEventType

def test_subscribe_and_publish_specific():
    el = EventListener()
    received = []
    def cb(ev):
        received.append(ev.type)
    el.subscribe(cb, [GameEventType.MOVE_REQUEST])
    el.publish(GameEvent(GameEventType.MOVE_REQUEST, source=None, payload={} ))
    el.publish(GameEvent(GameEventType.MOVE_COMPLETE, source=None, payload={} ))
    assert received == [GameEventType.MOVE_REQUEST]

def test_subscribe_all():
    el = EventListener()
    received = []
    def cb(ev):
        received.append(ev.type)
    el.subscribe(cb)
    el.publish(GameEvent(GameEventType.MOVE_REQUEST, source=None, payload={} ))
    el.publish(GameEvent(GameEventType.MOVE_COMPLETE, source=None, payload={} ))
    assert received == [GameEventType.MOVE_REQUEST, GameEventType.MOVE_COMPLETE]
