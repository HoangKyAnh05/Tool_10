"""Structured, separate expertise and retention plans for the livestream sample."""

def sample_plans():
    expertise=[
        ('0–2','Xác định hiểu nhầm','Đặt câu hỏi: 55% → 35% có phải giảm 20% không? Yêu cầu nêu phép tính, chưa mở đáp án.','Ghi lựa chọn ban đầu để đối chiếu sau khi giải thích.'),
        ('2–5','Kiểm tra đơn vị','Yêu cầu tự tính chênh lệch hai tỷ lệ rồi xác định đơn vị. So sánh thay đổi tuyệt đối với thay đổi tương đối.','Phải nêu được đơn vị và lý do chọn mẫu số ban đầu.'),
        ('5–10','Công thức và ví dụ','Viết hai công thức: sau − trước; (sau − trước)/trước × 100%. Áp dụng cho xe đạp 10% → 20%, rồi viết một câu tiếng Anh.','Kiểm tra phép tính, mẫu số, đơn vị và cách diễn đạt nhất quán.'),
        ('10–14','Bài chuyển giao cho người giỏi','Giao 40% → 50%: giải theo hai cách, giải thích vì sao cùng một chênh lệch chưa chắc có cùng mức thay đổi tương đối. Hỏi thêm điều gì xảy ra khi tỷ lệ ban đầu bằng 0.','Người xem tự giải thích được quy tắc và giới hạn, thay vì chỉ nhớ ví dụ.'),
        ('14–18','Sửa cách diễn đạt','Dùng 80% → 60%: cho hai câu dùng percent và percentage points, yêu cầu chọn câu đúng và sửa câu còn lại.','Đối chiếu đơn vị trong câu với phép tính; ghi nhận hiểu nhầm còn tồn tại.'),
        ('18–20','Kiểm tra cuối buổi','Yêu cầu nói một câu tiếng Anh cho một ví dụ đã học, rồi nêu cách tự kiểm tra mẫu số và đơn vị.','Một câu exit ticket có lý do; lời giải đầy đủ nằm trong tab Đáp án.'),
    ]
    retention=[
        ('0–2','Trò “Bắt lỗi máy tính”','“Tôi từng đổ oan cho máy tính vì một dấu %. Bạn chọn 1 đúng hay 2 sai? Ba phút nữa mình kiểm chứng; người biết rồi hãy đoán vì sao người mới nhầm.”','Ghi lựa chọn/bình luận nếu có. Không có bình luận: đặt hai phương án trên bảng để người xem tự chọn.'),
        ('2–5','Mở lời giải đúng hẹn','Đọc lý do của cả hai đội, đùa nhẹ với lỗi của chính mình, rồi mở lời giải đúng mốc đã hứa. Nối: “Trò đố là cửa vào; giờ cùng xem cơ chế.”','Đánh dấu đã trả lời đúng hẹn. Không chê người sai; không kéo dài để giữ người xem bằng chờ đợi.'),
        ('5–10','Cho người mới cùng tham gia','Mời viết một câu tiếng Anh trong 20 giây. “Nếu chưa chắc, bắt đầu bằng: The share of cyclists…” Không bình luận: tự minh họa một câu và nói rõ đó là ví dụ.','Ghi số câu trả lời thực tế hoặc ghi diễn thử một mình, chưa có số liệu.'),
        ('10–14','Mời người giỏi kiểm chứng','“Ai giải được hãy nói vì sao, đừng chỉ thả đáp án. Có trường hợp nào công thức không dùng được?” Đọc một phản biện rồi nối về ví dụ dễ hơn.','Ghi một lập luận hoặc câu phản biện có thật; không tự tạo tên người bình luận.'),
        ('14–18','Quay lại trò giữ chân chủ lực','“Lần này máy tính có lại bị oan không?” Cho chọn hai cách diễn đạt, mời một lời giải ngắn. Nếu im lặng, dùng hai phản hồi giả định và nói rõ là minh họa.','Kiểm tra người mới vẫn theo được; yếu tố hài hước phải phục vụ bài học.'),
        ('18–20','Chốt giá trị và mời hành động','“Lưu bảng, thử nói một câu, rồi kiểm tra mẫu số. Người đã giỏi hãy đề xuất một bẫy để buổi sau kiểm chứng.” Kết thúc đúng giờ.','Nếu live thật: log người xem tại 2/5/10/14/18/20 phút và watch time nếu nền tảng có. Diễn thử: ghi chưa đo giữ chân thực tế.'),
    ]
    def rows(items):
        return [dict(time=t,focus=f,script=s,check=c) for t,f,s,c in items]
    return rows(expertise),rows(retention)
