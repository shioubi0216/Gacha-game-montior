自動完成 Git commit 流程。

步驟：
1. 執行 `git status` 查看所有變更檔案
2. 執行 `git diff` 和 `git diff --staged` 查看具體變更內容
3. 執行 `git log --oneline -5` 參考最近的 commit message 風格
4. 根據變更內容，生成繁體中文的 commit message（格式：`type: 簡短描述`）
   - feat: 新功能
   - fix: 修正
   - refactor: 重構
   - docs: 文件
   - style: 樣式/格式
5. 將相關檔案加入 staging（不要加入 .env、credentials 等敏感檔案）
6. 執行 `git commit`
7. 顯示 commit 結果

注意：
- 不要自動 push，除非使用者明確要求
- commit message 用繁體中文
- data/games.json 已在 .gitignore，不需要 commit
