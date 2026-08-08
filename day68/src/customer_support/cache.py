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


class CachedApplication:
    """只缓存知识问答；订单查询等动态工具路径继续实时执行。"""

    def __init__(self, application, cache: AnswerCache):
        self.application = application
        self.cache = cache

    def handle(self, question, **kwargs):
        if kwargs.get("order_id"):
            return self.application.handle(question, **kwargs)
        tenant = kwargs.get("tenant_id", "local")
        version = kwargs.get("version", "v1")
        cached = self.cache.get(tenant, version, question)
        if cached is not None:
            return cached
        result = self.application.handle(question, **kwargs)
        self.cache.put(tenant, version, question, result)
        return result

    def ask(self, question, **kwargs):
        return self.handle(question, **kwargs).answer

    def __getattr__(self, name):
        return getattr(self.application, name)
