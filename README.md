# Hourly Coach

Ứng dụng luyện tập chạy nền trên Windows. Mỗi giờ tròn có một đề đầy đủ trong app; làm bài, nộp DOCX/text/ảnh/audio, xem đáp án và đánh giá trên laptop. Telegram chỉ gửi thông báo có đề mới hoặc chấm xong. Dữ liệu lưu tại máy.

## Cài và bắt đầu

1. Clone mã nguồn rồi chạy `INSTALL.ps1` bằng PowerShell. Script tạo môi trường Python, shortcut Desktop và shortcut Startup cho Windows.
2. Mở shortcut **Hourly Coach** → **Cài đặt kết nối**. Chọn Codex Chat và kiểm tra kết nối. Cần Codex được cài, đăng nhập ChatGPT và chat riêng cho gateway. Xem [CODEX-CHAT.md](CODEX-CHAT.md). Antigravity localhost là nguồn thay thế.
3. Xem **Đề mẫu để duyệt** và mở đáp án tham khảo khi cần. Duyệt cấu trúc đề để bật lịch tại giờ tròn kế tiếp.
4. Nút **Bật/Dừng tạo đề tự động** nằm ở đầu mọi màn hình. Dừng lịch vẫn giữ đề/bài nộp và tiếp tục chấm bài đã gửi; bật lại bắt đầu từ giờ tròn kế tiếp.
5. Vào **Lộ trình mỗi ngày** → chọn đề → **Bài nộp** → đính kèm bài → **Nộp & chấm toàn bộ**. Xem các tab Đề bài, Bài nộp, Đánh giá và Đáp án.
6. Telegram tùy chọn: tạo bot riêng trong [BotFather](https://t.me/BotFather), lưu token trong app, mở link ghép và bấm **Start**. Quay lại app kiểm tra ghép rồi thử thông báo. Không dùng chung bot với một ứng dụng đang polling hoặc có webhook.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\INSTALL.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\INSTALL-SPEECH.ps1
```

Script thứ hai cài chép lời audio bằng faster-whisper. `START.bat` mở app; `DISABLE-STARTUP.ps1` bỏ shortcut tự chạy khi đăng nhập Windows.

## Lịch và chạy nền

Ví dụ bật lúc 03:26 → đề đầu lúc 04:00, tiếp theo 05:00. App chuẩn bị đề đầu ngay khi bật, các đề sau trước giờ đến hạn 15 phút. AI/audio/mạng chậm có thể khiến đề đến trễ; lỗi được lưu và có nút thử lại. Không dùng đề/điểm giả để thay cho lỗi.

Đóng tab vẫn chạy nền. Startup mở Hourly Coach khi đăng nhập Windows; không cần mở giao diện. Chuột phải biểu tượng ở khay hệ thống → **Thoát ứng dụng** để tắt hoàn toàn. Sau khi thoát, mở lại shortcut Hourly Coach để chạy server. Việc mở Codex riêng không khởi động Hourly Coach.

Máy phải đang bật, có mạng và phiên Codex còn dùng được. Máy ngủ/tắt không tạo đề. Mở lại chỉ xử lý một lượt đến hạn, không gửi dồn các giờ đã bỏ lỡ. Lịch theo UTC+7. Server chỉ nghe localhost; Render Static Site không chạy scheduler, lưu dữ liệu hay gọi Codex trên laptop. Phiên bản này dùng app Windows, chưa có truy cập từ điện thoại hoặc backend cloud.

## Bộ đề

24 lượt luân phiên chín nhóm: IELTS, Cầu lông, Content, Edit, Bán hàng, Dạy, Quay 100 source, Tạo dịch vụ gói gọn và Livestream. IELTS có đủ bốn kỹ năng qua các lượt riêng:

| Kỹ năng | Đầu ra của đề |
|---|---|
| Listening | 4 section, 40 câu, audio TTS và đáp án; transcript chỉ mở trong đáp án |
| Reading | 3 passage tự viết, 40 câu và giải thích từng câu |
| Writing | Task 1 + Task 2, biểu đồ PNG vẽ từ số liệu thực hành và hai bài mẫu |
| Speaking | Part 1 đầy đủ câu hỏi, cue card Part 2 với bốn gợi ý/hai follow-up, Part 3 thảo luận và lời đáp cho từng câu |

Mỗi lượt luyện 60 phút. Speaking có lượt diễn thử 11–14 phút trong khung luyện, theo [cấu trúc IELTS Speaking](https://ielts.org/take-a-test/test-types/ielts-academic-test/ielts-academic-format-speaking). Câu hỏi mẫu tự biên soạn, không phải đề thi chính thức hay band được chứng nhận.

Nội dung đề trình bày bằng bảng. Livestream có hai bảng riêng **Chuyên môn** và **Giữ chân**, cùng mốc phút để đối chiếu. Mỗi đề có mục tiêu, đủ nguyên liệu, bước làm, bài cần nộp, rubric 100 điểm và đáp án đầy đủ tách khỏi đề.

## Nộp bài và đánh giá

Ưu tiên DOCX vì giữ chữ, bảng và ảnh. Có thể nộp text, ảnh và audio trong app. Google Docs/Drive hiện chưa tích hợp; xuất DOCX từ tài liệu rồi đính kèm. `.doc`, PDF và video chưa được hỗ trợ trực tiếp. Mỗi file tối đa 20 MB, mỗi lượt tối đa 40 ảnh và 120.000 ký tự sau trích xuất.

Ghi có/không tham khảo đáp án. Bài và file gốc được lưu trước khi AI chấm. Ảnh được phân tích riêng và giữ thứ tự. Nội dung tài liệu là dữ liệu cần đánh giá, không phải chỉ dẫn để thực thi mã hoặc mở link.

Speaking audio được chép lời cục bộ. Pronunciation cần người nghe bản ghi thực tế bổ sung; transcript không chứng minh phát âm. Kỹ thuật vận động, âm thanh/edit và giữ chân livestream cần bằng chứng phù hợp. Nếu thiếu, app ghi chưa chấm đủ và không tự kết luận năng lực. Có thể bổ sung điểm từ người nghe/xem, nguồn đánh giá được ghi riêng.

## Tiến bộ và độ khó

Độ khó tăng 10% sau một chu kỳ đủ 24 bài được chấm đủ, điểm trung bình ≥80/100; nếu chưa đạt, giữ mức. Hệ số tối đa 3×; thời lượng vẫn 60 phút. Tăng độ khó không chứng minh người học giỏi hơn 10%.

So sánh tiến bộ chỉ dùng cùng nhóm/kỹ năng/độ khó, tối thiểu ba bài mỗi ngày và tự khai không xem đáp án. Đây là ước lượng từ rubric, không phải phép đo năng lực chuẩn hóa hoặc cam kết tăng 10% mỗi ngày.

## Dữ liệu và kiểm thử

SQLite, uploads, submissions, assignments và lịch sử nằm trong `data/`, không đưa lên GitHub. Key/token được mã hóa Windows DPAPI; chuyển máy/tài khoản Windows cần nhập lại. Thoát app trước khi sao lưu cả thư mục dữ liệu. Không chia sẻ `session.json`.

API giao diện kiểm tra session, Host, Origin và CSRF; `/ask` yêu cầu key riêng. Key/token không trả lại trong state/log. Tin Telegram đã gửi được ghi nhận; kết quả gửi chưa xác định không tự gửi lại để tránh trùng.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
node --check web\app.js
node tests\test_ui.cjs
```

Các kiểm thử tự động dùng môi trường tạm và mô phỏng dịch vụ bên ngoài, không chứng minh một tài khoản Telegram/Codex cụ thể còn hoạt động. Trạng thái kết nối thực được xem trong app.
