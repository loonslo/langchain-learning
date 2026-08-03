"""租户+知识库版本+规范化问题组成缓存键，防止跨租户和旧政策命中。"""


class AnswerCache:
    def __init__(self, ttl, clock):
        self.ttl, self.clock, self.data = ttl, clock, {}

    def key(self, tenant, version, question):
        return tenant, version, " ".join(question.casefold().split())

    def put(self, tenant, version, question, value):
        self.data[self.key(tenant, version, question)] = (
            value,
            self.clock() + self.ttl,
        )

    def get(self, tenant, version, question):
        item = self.data.get(self.key(tenant, version, question))
        return item[0] if item and item[1] > self.clock() else None
