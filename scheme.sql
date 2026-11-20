-- ==========================================
-- 1151 軟體工程學期專案 - 共用資料庫結構 (schema.sql)
-- ==========================================

-- 清除舊表（方便開發期重新重置測試資料）
DROP TABLE IF EXISTS courses CASCADE;
DROP TABLE IF EXISTS bookings CASCADE;
DROP TABLE IF EXISTS rooms CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- 1. 共用帳號資料表 (支援註冊、管理員審核、多角色權限)
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,          -- 登入帳號（如學號或教師編號）
    password_hash VARCHAR(255) NOT NULL,           -- 密碼（建議存雜湊值，測試期可先存明文或簡易雜湊）
    full_name VARCHAR(50) NOT NULL,                -- 姓名
    email VARCHAR(100) UNIQUE NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'student',   -- 角色: 'admin'(管理員), 'teacher'(老師), 'student'(學生)
    account_status VARCHAR(20) NOT NULL DEFAULT 'pending', -- 帳號審核狀態: 'pending'(待審核), 'approved'(已通過), 'rejected'(已退件)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. 管院空間/教室資料表 (模組一：空間查詢模組)
CREATE TABLE rooms (
    room_id SERIAL PRIMARY KEY,
    room_code VARCHAR(20) UNIQUE NOT NULL,         -- 教室編號（如 'M202', 'MB01'）
    room_name VARCHAR(100) NOT NULL,               -- 教室名稱（如 '管院202一般教室', '管院B01演講廳'）
    floor VARCHAR(20) NOT NULL,                    -- 樓層（如 '2F', 'B1'）
    capacity INT NOT NULL DEFAULT 40,              -- 容納人數
    equipment TEXT,                                -- 教室基本設備說明（投影機、冷氣、麥克風等）
    panorama_url VARCHAR(255),                     -- 360全景照片路徑或網址 (給 Pannellum 讀取)
    map_x FLOAT,                                   -- 管院平面圖 X 座標百分比 (0~100)
    map_y FLOAT,                                   -- 管院平面圖 Y 座標百分比 (0~100)
    is_active BOOLEAN DEFAULT TRUE,                -- 是否開放使用
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. 空間/物品預約借用資料表 (模組二：預約借用模組)
CREATE TABLE bookings (
    booking_id SERIAL PRIMARY KEY,
    room_id INT NOT NULL REFERENCES rooms(room_id) ON DELETE CASCADE,
    user_id INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    booking_date DATE NOT NULL,                    -- 借用日期 (YYYY-MM-DD)
    start_time TIME NOT NULL,                      -- 開始時間 (如 '09:00:00')
    end_time TIME NOT NULL,                        -- 結束時間 (如 '12:00:00')
    borrowed_items TEXT[],                         -- 多選借用物品陣列（如 ARRAY['鑰匙', '投影筆', '筆電']）
    purpose VARCHAR(255),                          -- 借用事由
    -- 審核流程
    review_status VARCHAR(20) NOT NULL DEFAULT 'pending', -- 'pending'(待審核), 'approved'(通過), 'rejected'(退件)
    review_comment TEXT,                           -- 管理員審核意見
    reviewed_by INT REFERENCES users(user_id),     -- 審核管理員 ID
    -- 領用與歸還流程
    pickup_status VARCHAR(20) NOT NULL DEFAULT 'not_picked', -- 'not_picked'(未領用), 'picked_up'(已註記借出), 'returned'(已確認歸還)
    picked_up_at TIMESTAMP,                        -- 實際領用時間
    returned_at TIMESTAMP,                         -- 實際歸還時間
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. 課程排課資料表 (模組三：課程排課模組)
CREATE TABLE courses (
    course_id SERIAL PRIMARY KEY,
    course_name VARCHAR(100) NOT NULL,             -- 課程名稱（如 '軟體工程', '資料庫管理'）
    teacher_id INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE, -- 授課老師 ID
    room_id INT REFERENCES rooms(room_id) ON DELETE SET NULL, -- 希望教室 / 指派教室 ID
    day_of_week INT NOT NULL CHECK (day_of_week BETWEEN 1 AND 7), -- 週一到週日（1~7）
    start_time TIME NOT NULL,                      -- 上課開始時間 (如 '09:10:00')
    end_time TIME NOT NULL,                        -- 上課結束時間 (如 '12:00:00')
    CHECK (end_time > start_time),
    schedule_status VARCHAR(20) NOT NULL DEFAULT 'requested', -- 'requested'(老師志願登記), 'assigned'(管理員已指派確認)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- 預設測試資料 (讓三個模組開工就能直接測試)
-- ==========================================

-- 預設帳號（密碼皆先設為 '123456' 方便前期測試）
INSERT INTO users (username, password_hash, full_name, email, role, account_status) VALUES
('admin', '123456', '管院系統管理員', 'admin@ncnu.edu.tw', 'admin', 'approved'),
('prof_wang', '123456', '王大明教授', 'wang@ncnu.edu.tw', 'teacher', 'approved'),
('prof_lin', '123456', '林美玲教授', 'lin@ncnu.edu.tw', 'teacher', 'approved'),
('s113213001', '123456', '測試學生一', 's113213001@mail1.ncnu.edu.tw', 'student', 'approved'),
('s113213002', '123456', '待審核學生', 's113213002@mail1.ncnu.edu.tw', 'student', 'pending');

-- 預設管院教室資料（含平面圖測試座標與 360 圖片路徑）
INSERT INTO rooms (room_code, room_name, floor, capacity, equipment, panorama_url, map_x, map_y) VALUES
('M202', '管院202一般教室', '2F', 60, '單槍投影機、電動布幕、無線麥克風、冷氣', '/static/pano/m202.jpg', 35.5, 42.0),
('M203', '管院203電腦教室', '2F', 50, '個人電腦50台、廣播系統、雙投影機', '/static/pano/m203.jpg', 58.0, 42.0),
('MB01', '管院B01階梯演講廳', 'B1', 120, '大型投影布幕、環繞音響、講桌電腦', '/static/pano/mb01.jpg', 50.0, 75.0);

-- 預設借用測試資料（讓組員 B 直接有週借用表畫面可看）
INSERT INTO bookings (room_id, user_id, booking_date, start_time, end_time, borrowed_items, purpose, review_status, review_comment, pickup_status) VALUES
(1, 4, CURRENT_DATE, '13:00:00', '15:00:00', ARRAY['鑰匙', '投影筆'], '專題小組討論', 'approved', '準時歸還即可', 'not_picked'),
(2, 4, CURRENT_DATE + INTERVAL '1 day', '18:00:00', '20:00:00', ARRAY['鑰匙', '筆電'], '系學會活動彩排', 'pending', NULL, 'not_picked');

-- 預設排課測試資料（刻意放兩筆同時段同教室，讓組員 C 測試時間衝突清單）
INSERT INTO courses (course_name, teacher_id, room_id, day_of_week, start_time, end_time, schedule_status) VALUES
('軟體工程', 2, 1, 3, '09:10:00', '12:00:00', 'assigned'),
('系統分析與設計', 3, 1, 3, '10:10:00', '12:00:00', 'requested');