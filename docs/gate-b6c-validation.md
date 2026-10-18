# B6c Gate 验证记录 · 2026-10-18

B6c 覆盖 9.2 槽位、9.3 JSON 契约、9.10 兼容配置；9.5 RLS、项目步骤/选修仍未做。

## 范围与结果

| 章节 | v2 | 验收项 | 参考解 |
|---|---|---|---|
| 9.2 槽位填充 | L9 | 5 | 5/5 |
| 9.3 稳定 JSON | L9 | 6 | 6/6 |
| 9.10 兼容配置 | L5.10 | 5 | 5/5 |

默认骨架 0 通过。

## 回归与结构检查

```text
pytest tools chapters/test_new_lessons.py -q：28 passed
check_course_links：275 个 Markdown，断链 0
apply_v2_map --check：111 unchanged
ruff：All checks passed
```

## 覆盖的故障

- **9.2**：订单号提取、previous 覆盖、缺失订单号、shipping 不追问、未知意图。
- **9.3**：围栏 JSON、bool/int 严格、多字段、非对象、repair 一次/失败。
- **9.10**：URL 拼接、base_url/`/v1`、model/env、生产 HTTPS。

## 未验证

- 临时参考解，不是学习记录；9.5 RLS 未做。
- 9.2 用正则不验证模型；9.3 不调模型；9.10 不发请求。

## 复现

```bash
python chapters/part9-enterprise-infra-optional/9.2-slot-filling/gate/gate_check.py
python chapters/part9-enterprise-infra-optional/9.3-stable-json-output/gate/gate_check.py
python chapters/part9-enterprise-infra-optional/9.10-openai-compatible-provider/gate/gate_check.py
```

## 边界

- B6 未完成：9.5、项目步骤/证据、10.x 待做。
- gate 只验证规则/契约，真实服务未验证。
