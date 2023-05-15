from fastsession.memory_store import MemoryStore

def test_has_session_id():
    """
    Test session ID presence in the store.

    ストア内のセッションIDの存在をテスト
    """
    store = MemoryStore()
    store.create_store("test-id")
    assert store.has_session_id("test-id")
    assert not store.has_no_session_id("test-id")

def test_get_store():
    """
    Test retrieval of the store.

    ストアの取得をテスト
    """
    store = MemoryStore()
    store.create_store("test-id")
    assert store.get_store("test-id") == {}
    assert store.get_store("nonexistent-id") is None
