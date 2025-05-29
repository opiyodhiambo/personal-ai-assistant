from uuid import uuid4


class MongoAtlasClient:
    def __init__(self):
        pass

    def save(self, documents):
        uuids = [str(uuid4()) for _ in range(len(documents))]

        pass