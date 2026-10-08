# Hourly Coach

Ứng dụng luyện tập chạy nền trên Windows. Mỗi giờ tròn mở trọn một bộ 12 đề đầy đủ trong app; làm bài, lưu text/ảnh/video/DOCX/audio ở cuối từng đề. Hoàn thành đủ 12 bài của cùng bộ rồi gửi cả bộ, nhận kết quả cùng lúc trên laptop. Telegram chỉ báo có đề mới hoặc chấm xong cả bộ. Dữ liệu lưu tại máy.

## Cài và bắt đầu

1. Clone mã nguồn rồi chạy `INSTALL.ps1` bằng PowerShell. Script tạo môi trường Python, shortcut Desktop và shortcut Startup cho Windows.
2. Mở shortcut **Hourly Coach** → **Cài đặt kết nối**. Chọn Codex Chat và kiểm tra kết nối. Cần Codex được cài, đăng nhập ChatGPT và chat riêng cho gateway. Xem [CODEX-CHAT.md](CODEX-CHAT.md). Antigravity localhost là nguồn thay thế.
3. Xem **Đề mẫu để duyệt** và mở đáp án tham khảo khi cần. Duyệt cấu trúc đề để bật lịch tại giờ tròn kế tiếp.
4. Nút **Bật/Dừng tạo đề tự động** nằm ở đầu mọi màn hình. Dừng lịch vẫn giữ đề/bài nộp và tiếp tục chấm bài đã gửi; bật lại bắt đầu từ giờ tròn kế tiếp.
5. Vào **Lộ trình mỗi ngày** → chọn đề → ô **Bài làm của bạn** ngay cuối đề. Lưu text và file, đánh dấu hoàn thành. Đủ **8 nhóm khác + 2 Writing + 2 Speaking = 12 đề** → **Bộ bài & chấm** → **Gửi tất cả & chấm**. Kết quả của cả bộ mở cùng lúc, đồng thời hiện dưới ô bài làm của từng đề. Lưu nháp không đưa bài đi chấm; server chặn gửi từng đề và chặn gửi bộ còn thiếu.
6. Telegram tùy chọn: tạo bot riêng trong [BotFather](https://t.me/BotFather), lưu token trong app, mở link ghép và bấm **Start**. Quay lại app kiểm tra ghép rồi thử thông báo. Không dùng chung bot với một ứng dụng đang polling hoặc có webhook.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\INSTALL.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\INSTALL-SPEECH.ps1
```

Script thứ hai cài chép lời audio bằng faster-whisper. `START.bat` mở app; `DISABLE-STARTUP.ps1` bỏ shortcut tự chạy khi đăng nhập Windows.

## Lịch và chạy nền

Ví dụ bật lúc 03:26 → đề đầu lúc 04:00, tiếp theo 05:00. App chuẩn bị trước giờ phát ít nhất 20 phút, tự tăng thời gian chuẩn bị dựa trên ba bộ gần nhất cộng khoảng đệm. Khi chưa đo được tốc độ, app dành cả giờ để chuẩn bị. Các yêu cầu AI chạy tuần tự; bộ được giữ ẩn và chỉ mở khi đến giờ và đủ cả 12 đề, đáp án và hình. AI/mạng chậm có thể khiến bộ đến trễ; lỗi được lưu và có nút thử lại. Không dùng đề/điểm giả để thay cho lỗi.

Đóng tab vẫn chạy nền. Startup mở Hourly Coach khi đăng nhập Windows; không cần mở giao diện. Chuột phải biểu tượng ở khay hệ thống → **Thoát ứng dụng** để tắt hoàn toàn. Sau khi thoát, mở lại shortcut Hourly Coach để chạy server. Việc mở Codex riêng không khởi động Hourly Coach.

Máy phải đang bật, có mạng và phiên Codex còn dùng được. Máy ngủ/tắt không tạo đề. Mở lại chỉ xử lý một lượt đến hạn, không gửi dồn các giờ đã bỏ lỡ. Lịch theo UTC+7. Server chỉ nghe localhost; Render Static Site không chạy scheduler, lưu dữ liệu hay gọi Codex trên laptop. Phiên bản này dùng app Windows, chưa có truy cập từ điện thoại hoặc backend cloud.

## Bộ đề

Mỗi giờ mở một bộ có **8 nhóm thực hành khác + 2 Writing + 2 Speaking**, tổng 12 đề. IELTS không tạo Listening/Reading. Bài lịch cũ được lưu riêng để xem lại.

Ngân hàng làm trước gồm **10 bộ × 12 = 120 đề** Codex biên soạn, có chủ đề và brief khác nhau; không phải 120 lượt gọi gateway hay đề thi chính thức. Bộ tự động tiếp theo được tạo mới qua AI đã cấu hình. App kiểm tra nội dung trùng, câu nghị luận, cue card và dữ liệu hình với lịch sử; khi không đạt sẽ yêu cầu AI tạo lại, tối đa ba lần, rồi ghi lỗi để thử tiếp. Kiểm tra này không bảo đảm phát hiện mọi cách diễn đạt cùng ý.

Máy đã cài ngân hàng có thể dùng ngay **Bộ bài & chấm → Bộ làm trước 1–10**. Khi cài mới từ mã nguồn, thoát app qua khay hệ thống rồi chạy `.\.venv\Scripts\python.exe SEED-PRACTICE-BANK.py` một lần. Chạy lại không thêm đề trùng và không tạo điểm/bài nộp giả.

| Kỹ năng | Đầu ra của đề |
|---|---|
| Writing | Đủ Task 1 + Task 2, hình PNG và hai bài mẫu đạt tối thiểu 150/250 từ |
| Speaking | Part 1 ít nhất 8 câu, cue card Part 2 với bốn gợi ý/hai follow-up, Part 3 ít nhất 6 câu và lời đáp tham khảo từng phần |

Task 1 luân phiên: **cột → đường → tròn → bảng → quy trình → bản đồ/mặt bằng → kết hợp → sơ đồ thiết bị**. Hai đề Writing liên tiếp khác dạng, kể cả qua ranh giới bộ. Dữ liệu, nhãn, sơ đồ và bài mẫu phải khớp nhau. Đây là các hình thực hành tự tạo dựa trên [các dạng IELTS Writing](https://ielts.org/take-a-test/preparation-resources/writing-test-resources), không phải số liệu chính thức.

Mỗi lượt luyện 60 phút. Speaking có lượt diễn thử 11–14 phút trong khung luyện, theo [cấu trúc IELTS Speaking](https://ielts.org/take-a-test/test-types/ielts-academic-test/ielts-academic-format-speaking). Câu hỏi mẫu tự biên soạn, không phải đề thi chính thức hay band được chứng nhận.

Nội dung đề trình bày bằng bảng. Livestream có hai bảng riêng **Chuyên môn** và **Giữ chân**, cùng mốc phút để đối chiếu. Mỗi đề có mục tiêu, đủ nguyên liệu, bước làm, bài cần nộp, rubric 100 điểm và đáp án đầy đủ tách khỏi đề.

## Nộp bài và đánh giá

Ưu tiên DOCX vì giữ chữ, bảng và ảnh. Có thể lưu text, ảnh, audio và video MP4/MOV/WebM/MKV trong app, rồi gửi khi đủ cả bộ. Google Docs/Drive hiện chưa tích hợp; xuất DOCX từ tài liệu rồi đính kèm. `.doc` và PDF chưa được hỗ trợ trực tiếp. Video tối đa 100 MB và 30 phút; file khác tối đa 20 MB. Mỗi bài tối đa 40 ảnh sau trích xuất và 120.000 ký tự. Cần chạy INSTALL-SPEECH.ps1 để có PyAV và faster-whisper cho audio/video.

Ghi có/không tham khảo đáp án. Bản nháp và file gốc được lưu trước khi gửi cả bộ. Khi đủ 12 bài trong cùng một bộ, app lưu bản gửi của cả bộ trong một giao dịch rồi xếp hàng chấm. Kết quả của từng bài được giữ lại cho đến khi cả bộ xong; Telegram chỉ gửi một thông báo kết quả. Nếu có lỗi, thử lại các bài lỗi mà không gửi lại các bài đã chấm. Ảnh được phân tích riêng và giữ thứ tự. Nội dung tài liệu là dữ liệu cần đánh giá, không phải chỉ dẫn để thực thi mã hoặc mở link.

Video được giải mã bằng PyAV, lấy tối đa 12 frame mẫu trải đều có timecode và trích âm thanh để chép lời. App ghi rõ bằng chứng đã đọc, không tuyên bố xem liên tục toàn bộ video hoặc nghe trực tiếp nhạc/giọng. Speaking audio được chép lời cục bộ. Pronunciation cần người nghe bản ghi thực tế bổ sung; transcript không chứng minh phát âm. Kỹ thuật vận động, âm thanh/edit và giữ chân livestream cần bằng chứng phù hợp. Nếu thiếu, app ghi chưa chấm đủ và không tự kết luận năng lực. Có thể bổ sung điểm từ người nghe/xem, nguồn đánh giá được ghi riêng.

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
