# ACL 变更未生效事故演练（Day73）

## 场景

文档正文未变化，但 ACL sidecar 从 `public` 收紧为 `restricted`。旧实现只计算正文哈希，增量同步没有更新向量 metadata，普通用户仍可能召回旧 chunk。

## 发现

- 权限负向回归或抽样审计发现未授权来源。
- 请求 trace 通过 `request_id` 定位知识版本、租户、用户角色和召回 chunk。
- 不在普通日志中复制问题、文档正文或 token。

## 止损

1. 关闭受影响租户问答或强制只返回拒答。
2. 使该租户缓存失效。
3. 暂停相关知识同步和发布。
4. 保留不含正文的审计证据。

## 修复与恢复

1. 将正文、ACL、parser、chunk 和 embedding 配置共同纳入 `source_version`。
2. 重建受影响租户索引并原子更新同步状态。
3. 重新运行跨租户、普通用户、部门和角色负向测试。
4. 重新运行引用评测，确认来源来自新知识版本。

## 永久动作

- `test_source_version_changes_when_acl_or_pipeline_changes` 成为永久回归。
- 发布评审检查 ACL 收紧、缓存失效和旧索引清理。
- 分布式摄取补充租约、失败事件和死信重放。
