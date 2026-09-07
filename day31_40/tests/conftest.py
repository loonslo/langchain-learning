def pytest_addoption(parser):
    parser.addoption("--run-online", action="store_true", default=False,
                     help="运行会消耗真实 LLM/搜索额度的在线集成测试")
