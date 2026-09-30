-- 通过事务本地变量传入已认证租户；应用连接必须不是表 owner / BYPASSRLS 角色。
CREATE TABLE IF NOT EXISTS conversation_messages (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS conversation_messages_scope_created_idx
    ON conversation_messages (tenant_id, user_id, session_id, created_at DESC);

ALTER TABLE conversation_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversation_messages FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS conversation_tenant_isolation ON conversation_messages;
CREATE POLICY conversation_tenant_isolation ON conversation_messages
    USING (tenant_id = current_setting('app.tenant_id', true))
    WITH CHECK (tenant_id = current_setting('app.tenant_id', true));
