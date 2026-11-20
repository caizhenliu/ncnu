-- ==========================================
-- 移除管院網站上不存在的測試教室（M202、MB01）
-- 依據：https://www.ibs.ncnu.edu.tw/index.php/resources/space-classroom
-- 已於 2026-11-20 在共用資料庫執行，這份檔案是紀錄用，重複執行不會有影響
--
-- 注意：bookings.room_id 是 ON DELETE CASCADE，courses.room_id 是 ON DELETE SET NULL
--   刪除時 M202 的 1 筆測試借用（專題小組討論）會一起被刪除
-- ==========================================
DELETE FROM rooms WHERE room_code IN ('M202', 'MB01');
