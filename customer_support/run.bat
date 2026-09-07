@echo off
REM 一键启动客服助手（后端 API + 前端静态站点）
REM 双击即可：会自动拉起服务并用浏览器打开页面。
cd /d "%~dp0"
set "TMPDIR=%~dp0.build"
set "HF_HUB_OFFLINE=1"
uv run python run.py
pause
