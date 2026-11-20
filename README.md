# ncnu
管院空間與排課系統（1151 軟體工程學期專案）

## 本機啟動
1. 安裝套件：`pip install fastapi uvicorn "psycopg[binary]" python-dotenv`
2. 複製 `.env.example` 為 `.env`，把 `[YOUR-DATABASE-PASSWORD]` 換成組內私下傳的密碼（`.env` 不會被上傳）
3. 啟動：`uvicorn main:app --reload --port 8001`
4. 開啟 http://127.0.0.1:8001

## 共用資料庫（Supabase）
- 三個模組都連同一個雲端 PostgreSQL，資料自動同步，不用各自建本機資料庫
- `scheme.sql` 是資料表結構與測試資料，**開頭會 DROP 所有表**，只在第一次建立或要整個重置時執行，執行前先在群組講
- 之後改結構請用 `ALTER TABLE`，不要重跑整份 `scheme.sql`
