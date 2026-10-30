# 用补丁交接一项自造任务

用途：在两个临时Git仓库之间，用`git format-patch`与`git am`交接一个提交，再运行恢复后的程序。仅演示可携带的代码改动；不连接Jules，不读取账号、密钥或真实项目，不承诺平台导出文件可以直接交给`git am`。

环境：Python 3.12.3、Git（本次实际版本见日期目录运行说明）；无第三方Python依赖，无网络请求或全局配置修改。临时目录结束后自动清理。

```bash
python3 handoff.py
```

真实输出见`expected.txt`。所有仓库、任务和代码都是本脚本自造；Git身份只用于临时命令，不使用用户身份。正式项目恢复补丁时，要核对基线、评审改动并重新测试。

参考：[Git format-patch](https://git-scm.com/docs/git-format-patch)、[Git am](https://git-scm.com/docs/git-am)、[Jules官方停用说明](https://jules.google/docs/changelog/2026-10-29)。
