from src.enterprise_support.benchmark import InferenceSlo, RequestSample, release_errors, summarize


def test_benchmark_reports_latency_ttft_throughput_and_error_rate():
    summary = summarize([
        RequestSample(100, 30, 10, True),
        RequestSample(200, 50, 20, True),
        RequestSample(900, 500, 0, False),
    ])
    assert summary.p95_latency_ms == 200
    # 当前函数按串行样本耗时计算；并发压测应另传真实 wall-clock 时间。
    assert summary.output_tokens_per_second == 100
    assert round(summary.error_rate, 2) == 0.33


def test_slo_gate_blocks_release_when_tail_or_error_rate_regresses():
    summary = summarize([RequestSample(100, 80, 5, True), RequestSample(500, 400, 5, True)])
    assert release_errors(summary, InferenceSlo(200, 100, 0)) == ("p95 总延迟超出 SLO", "p95 TTFT 超出 SLO")
