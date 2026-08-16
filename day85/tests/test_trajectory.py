from ai_testing.trajectory import TraceStep, TrajectoryPolicy, validate_trajectory


POLICY = TrajectoryPolicy(frozenset({"get_order", "create_ticket"}), write_tools=frozenset({"create_ticket"}))


def test_read_only_order_trajectory_is_allowed():
    steps = [
        TraceStep(1, "retrieve"),
        TraceStep(2, "tool", "get_order", arguments={"order_id": "A1"}),
        TraceStep(3, "respond"),
    ]

    assert validate_trajectory(steps, POLICY) == []


def test_trajectory_rejects_unauthorized_and_unapproved_write_tools():
    steps = [
        TraceStep(1, "tool", "delete_order"),
        TraceStep(2, "tool", "create_ticket", approved=False),
    ]

    errors = validate_trajectory(steps, POLICY)

    assert "工具未授权" in errors[0]
    assert any("写操作缺少审批" in error for error in errors)


def test_trajectory_has_a_step_budget():
    steps = [TraceStep(index, "retrieve") for index in range(1, 8)]

    assert any("最大步骤数" in error for error in validate_trajectory(steps, POLICY))
