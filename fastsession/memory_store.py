import time


class MemoryStore:
    def __init__(self):
        """
        Initialize an instance of MemoryStore. Create a dictionary to store the data for each session.

        MemoryStoreのインスタンスを初期化し、各セッションのデータを格納する辞書を作成する
        """

        self.raw_memory_store = {}

    def has_session_id(self, session_id):
        """
        Check if the session_id key exists in the store.

        storeにsession_idキーが存在するか確認する

        :param session_id: Session ID to check
        :return: True if the session_id exists, False otherwise
        """

        return session_id in self.raw_memory_store

    def has_no_session_id(self, session_id):
        """
        Check if the session_id key does not exist in the store.

        storeにsession_idキーが存在しないか確認する

        :param session_id: Session ID to check
        :return: True if the session_id does not exist, False otherwise
        """
        return session_id not in self.raw_memory_store

    def create_store(self, session_id):
        """
        Create a new store for the given session_id.

        与えられたsession_idの新しいstoreを作成する

        :param session_id: Session ID for which to create a store
        :return: The newly created store
        """
        self.raw_memory_store[session_id] = {
            "created_at": int(time.time()),  # Current UNIX time,
            "store": {}}
        self.save_store(session_id)  # 永続化
        return self.raw_memory_store.get(session_id).get("store")

    def get_store(self, session_id):
        """
        Get the store for the given session_id.

        与えられたsession_idのstoreを取得する

        :param session_id: Session ID for which to get the store
        :return: The store corresponding to the session_id, or None if no such store exists
        """

        if self.raw_memory_store.get(session_id):
            return self.raw_memory_store.get(session_id).get("store")
        else:
            return None

    def save_store(self, session_id):
        """
        Persist the store for the given session_id. As this is an in-memory store,
        the data will not persist across application restarts.

        これが、物理ストレージにひもづいているストアの場合、
        与えられたsession_idのstoreを永続化する。
        ただし、いまこれはオンメモリのストアなので、
        アプリケーションの再起動をまたいでデータは永続化されない。

        :param session_id: Session ID for which to persist the store
        """
        session_store = self.get_store(session_id)
        if session_store:
            # 本ストアは
            # メモリベースなので、とくになにもしない
            pass

    def gc(self):
        # メモリストアに100件以上のセッションデータがあるばあい、古いものを削除する
        if len(self.raw_memory_store) >= 100:
            self.cleanup_old_sessions()

    def cleanup_old_sessions(self):
        current_time = int(time.time())
        sessions_to_delete = []
        for session_id, session_info in self.raw_memory_store.items():
            if current_time - session_info["created_at"] > 3600 * 12:  # 作成から12時間を経過したセッションデータは削除する
                sessions_to_delete.append(session_id)

        for session_id in sessions_to_delete:
            del self.raw_memory_store[session_id]
