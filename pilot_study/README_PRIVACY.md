# Pilot Study 隐私与数据管理

为防止实验数据泄露，本目录下的所有内容（数据与输出）已在仓库根 `.gitignore` 中设置忽略，不会被 Git 跟踪和提交。仅保留分析脚本 `analyze_pilot_study.py` 作为受控代码。

## 当前策略
- 忽略原始与中间数据（如 `*.txt`, `*.h5`, `*_EventsAnnotation.txt`）
- 忽略派生输出（如 `outputs/` 下的图像、CSV、JSON）
- 分析脚本留在版本控制中，便于复用与协作

## 如果已有敏感文件被 Git 跟踪
执行以下命令将其从索引中移除（不删除本地文件），然后再提交：

```bash
git rm -r --cached pilot_study
git add pilot_study/analyze_pilot_study.py pilot_study/README_PRIVACY.md
git commit -m "Stop tracking pilot_study data; keep analysis script and privacy README"
```

注意：请确认你的远程仓库策略（public/private）。公开仓库请务必确保不推送任何敏感数据文件。

## 建议
- 将敏感数据保存在私有存储（本地、私有云盘或私有仓库的 LFS），不要放入公共仓库。
- 如需共享结果，优先共享汇总统计（不含可识别个人来源的原始数据）。
