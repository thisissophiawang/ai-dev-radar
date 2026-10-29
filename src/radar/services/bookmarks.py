import uuid


class Bookmarks:
    def __init__(self, store):
        self.store = store

    def save(self, item_id, note, request_key=None):
        return self.store.bookmark_write('save',item_id,note,request_key if request_key is not None else uuid.uuid4().hex)

    def remove(self, item_id, request_key=None):
        return self.store.bookmark_write('remove',item_id,'',request_key if request_key is not None else uuid.uuid4().hex)
