"""Human-authored previews. Not labeled as AI-generated or submitted results."""
from .curriculum import rubric_for
from .solutions import add_solutions

WRITING = dict(
    category='IELTS',skill='Writing',title='Một giờ Writing: biểu đồ rõ ràng, lập luận có chiều sâu',
    objective='Hoàn thành đủ hai task Academic trong 60 phút, mức luyện 6.5 → 8.0; so sánh dữ liệu chính xác và phát triển lập luận có phản biện.',
    duration_minutes=60,
    chart={'type':'bar','title':'How adults commuted to work: 2005 and 2025','unit':'%',
      'categories':['Private car','Bus','Bicycle','On foot'],
      'series':[{'name':'2005','values':[55,25,10,10]},{'name':'2025','values':[35,30,20,15]}],
      'source_note':'Practice dataset created for this exercise. Percentages in each year total 100%.'},
    materials='Dữ liệu GIẢ LẬP cho Task 1: tỷ lệ người trưởng thành đi làm bằng bốn phương tiện trong một thành phố năm 2005 và 2025.\nPhương tiện | 2005 | 2025\nÔ tô riêng | 55% | 35%\nXe buýt | 25% | 30%\nXe đạp | 10% | 20%\nĐi bộ | 10% | 15%\nMỗi cột tổng 100%. Đây là cơ cấu tỷ lệ, không phải số người tuyệt đối.',
    instructions='Task 1: 3 phút đọc và nhóm xu hướng, 14 phút viết, 3 phút soát; Task 2: 5 phút lập dàn ý, 30 phút viết, 5 phút soát. Viết bằng tiếng Anh. Không dùng AI/tra từ trong lượt đo đầu. Nêu số từ và thời gian thực tế. Không suy ra nguyên nhân từ bảng nếu đề không cung cấp. Mỗi đoạn thân Task 2 cần claim → explanation → example → implication.',
    writing_tasks=[
        'Task 1 (20 minutes, at least 150 words). The bar chart compares the percentages of adults using four modes of transport to commute in a city in 2005 and 2025. Summarise the information by selecting and reporting the main features, and make comparisons where relevant.',
        'Task 2 (40 minutes, at least 250 words). Some people believe that governments should invest more in public transport than in building new roads. To what extent do you agree or disagree? Give reasons for your answer and include relevant examples from your own knowledge or experience.'],
    deliverables='Gửi 1 file DOCX: mã bài ở dòng đầu; Task 1 đầy đủ; Task 2 đầy đủ; số từ từng task; thời gian; ghi rõ có dùng tài liệu hỗ trợ hay không. Có thể thêm ảnh dàn ý, nhưng chữ trong bài phải là text. Reply tin đề để tránh nhầm bài.',
    rubric=rubric_for('IELTS','Writing'),
    answer_key='''TASK 1 — BÀI THAM KHẢO
The bar chart compares the proportions of working adults who travelled to work by car, bus, bicycle and on foot in a city in 2005 and 2025.

Overall, private cars remained the most common means of commuting, although their share fell substantially over the period. By contrast, all three alternatives became more popular, with cycling recording the largest increase among them. The combined share of these alternatives rose from a minority to a clear majority.

In 2005, 55% of adults commuted by car, more than twice the proportion using buses, at 25%. Cycling and walking each accounted for just 10%, making them the least frequently used modes. Together, non-car journeys represented 45% of commuting trips.

By 2025, the figure for cars had declined by 20 percentage points to 35%, while bus use had increased to 30%. The gap between these two modes therefore narrowed from 30 to five percentage points. Meanwhile, the share of cyclists doubled to 20%, and the proportion walking rose by five percentage points to 15%. Taken together, the three alternatives accounted for 65% of commuters in the later year.

TASK 2 — BÀI THAM KHẢO
Governments often face a choice between expanding roads and improving public transport. I largely agree that the latter deserves a greater share of investment, particularly in crowded cities, although essential road maintenance and carefully selected rural projects should continue.

The strongest argument for prioritising public transport is that it can move large numbers of people while using relatively little urban space. A reliable bus or rail service gives commuters a practical alternative to driving, reducing the demand for parking and allowing streets to accommodate pedestrians and commercial activity. However, this benefit depends on service quality. A new rail line is unlikely to attract many passengers if stations are difficult to reach or trains run infrequently. Investment should therefore include affordable fares, dependable timetables and connections between different modes, rather than focusing exclusively on expensive infrastructure.

Public transport can also improve access to employment and education for people who cannot afford a car. For example, a frequent bus route linking residential districts to a college may allow students to attend classes without depending on relatives for transport. Spending that enables these journeys serves a wider social purpose than adding another lane primarily for existing motorists. Nevertheless, routes should be planned using actual travel needs; an impressive network offers limited value if it fails to reach the places where people work and study.

There are circumstances in which road investment remains necessary. Rural communities may lack the population density needed to support frequent scheduled services, and unsafe roads can prevent emergency vehicles or deliveries from reaching them. In these cases, repairing dangerous sections and improving essential connections may produce greater benefits than introducing underused bus services.

In conclusion, governments should generally give public transport priority in urban budgets while retaining targeted funding for road safety and rural access. The appropriate balance should reflect local needs and measurable improvements in mobility, rather than a blanket preference for one type of infrastructure.

PHÂN TÍCH: Task 1 cần overview và chênh lệch theo điểm phần trăm; không đổi 55% thành 55 người, không nói car giảm 20%. Task 2 giữ quan điểm rõ, giải thích điều kiện vận hành và ngoại lệ, không chỉ liệt kê ưu điểm. Bài mẫu là hướng tham khảo, không phải đáp án duy nhất. Bốn tiêu chí dùng cùng thang 25 điểm. Task 2 trọng số 2, Task 1 trọng số 1; band do AI ước lượng, không phải điểm thi chính thức.''')

def example(category,title,objective,materials,instructions,deliverables,answer):
    return dict(category=category,skill='',title=title,objective=objective,duration_minutes=60,
       materials=materials,instructions=instructions,deliverables=deliverables,
       answer_key=answer,rubric=rubric_for(category,''))


def samples():
    shots=[]
    groups=['Toàn cảnh không gian','Sản phẩm chính','Chi tiết vật liệu','Tay sử dụng','Trước / sau','Đóng gói','Chuyển động','Góc nhìn người dùng','Ánh sáng / bóng','Cảnh kết thúc']
    variants=['chính diện tĩnh','góc 45 độ','ngang tầm mắt','từ trên xuống','cận cảnh','siêu cận','pan trái → phải','tilt dưới → trên','đẩy máy chậm','rút máy chậm']
    for g,group in enumerate(groups):
        for v,variant in enumerate(variants):
            n=g*10+v+1
            shots.append(f'{n:03d} | {group} · {variant} | 3–5 giây | SRC_{n:03d}.mp4')
    data=[dict(WRITING),
      example('Cầu lông','Footwork 6 điểm: đo độ ổn định, không chỉ số lần',
       'Ghi được 5 hiệp di chuyển, tỷ lệ đúng điểm chạm và 2 lỗi có bằng chứng; giữ cường độ nhẹ phù hợp thể lực.',
       'Vợt, điện thoại, sáu dấu sàn không trơn quanh vị trí giữa sân. Không có sân: thu nhỏ vùng đi và đi bộ mô phỏng. Mẫu log: hiệp | 12 lần chạm | đúng điểm | mất thăng bằng | cảm nhận gắng sức 1–10.',
       '0–8 phút khởi động nhẹ; 8–13 phút đặt 6 dấu và tập chậm; 13–33 phút 5 hiệp × 12 lần, nghỉ 60–90 giây giữa hiệp; 33–43 phút xem bằng chứng; 43–53 phút sửa 1 lỗi ở tốc độ thấp; 53–60 phút ghi log. Trở về giữa sau mỗi lần chạm, không nhảy cao. Nếu đau/chóng mặt thì dừng. Tỷ lệ ổn định = số lần đúng điểm không mất thăng bằng / 60 × 100%.',
       'DOCX chứa log 5 hiệp, 6 ảnh liên tiếp có timestamp cho một lần di chuyển, tỷ lệ ổn định, 2 lỗi và 1 điều chỉnh. Ảnh tĩnh chỉ hỗ trợ quan sát tư thế; tốc độ và nhịp cần người xem video xác minh.',
       'Đầu ra đạt: đủ 60 lần có log, tính đúng tỷ lệ, mô tả lỗi gắn ảnh. Ví dụ GIẢ LẬP 48/60 = 80%. Sửa bước cuối quá dài bằng giảm khoảng cách, ưu tiên thăng bằng. Không khẳng định kỹ thuật đạt chỉ vì hoàn thành số lần.'),
      example('Content','Viết video 45 giây cho lớp cầu lông người mới',
       'Tạo 3 hook khác nhau, 1 kịch bản có giá trị cụ thể và 1 giả thuyết thử nghiệm.',
       'Brief GIẢ LẬP: lớp cho người 20–35 tuổi mới tập, 4 buổi/khóa, 60 phút/buổi, nhóm tối đa 6, giá 800.000đ; có buổi trải nghiệm 100.000đ được trừ học phí nếu đăng ký. Không cam kết thành tích hay kết quả sức khỏe.',
       '0–10 phút chọn 1 nỗi lo người mới; 10–20 viết 3 hook (câu hỏi, đối lập trải nghiệm, minh họa lỗi); 20–40 viết kịch bản 120–150 từ với hình/thoại/thời lượng; 40–50 viết caption 80–120 từ và CTA; 50–60 lập test A/B chỉ thay hook. Nêu metric giữ người xem ở giây 3 và click đăng ký; không bịa số liệu đã chạy.',
       'DOCX: audience insight, 3 hook, bảng kịch bản 0–45 giây, caption, CTA, biến test và quy tắc lựa chọn sau tối thiểu 1.000 impressions mỗi biến thể.',
       'Hook mẫu: “Bạn không cần đánh mạnh để bắt đầu buổi đầu tiên.” Thân: minh họa tư thế → bài tập nhỏ → giới thiệu nhóm 6 → lời mời trải nghiệm. CTA: gửi TẬP để nhận lịch. Test dự kiến, không gán kết quả thực tế khi chưa xuất bản.'),
      example('Edit','Dựng 30 giây từ 8 source tự quay',
       'Đầu ra có mạch đầu–giữa–kết, thoại rõ và checklist xuất file có bằng chứng.',
       '8 clip nguồn: cảnh rộng, mặt sản phẩm, tay mở, chi tiết, dùng thử, phản ứng, đóng gói, cảnh kết. Có thể tự quay đồ vật tại nhà. Dùng trình dựng bạn có; nhạc tự tạo hoặc được phép dùng. Không cần công cụ trả tiền.',
       '0–10 quay/lựa 8 clip; 10–18 chọn 1 thông điệp; 18–38 dựng 30 giây (hook 0–3, chứng minh 3–23, kết 23–30); 38–48 kiểm âm/subtitle; 48–55 xuất 1080×1920, H.264, 30 fps; 55–60 chụp timeline và ghi quyết định. Không che vùng chữ quan trọng bằng phụ đề.',
       'DOCX: storyboard, 6 ảnh timeline/frame có timecode, thông số xuất, mô tả xử lý âm thanh và tự kiểm. Muốn xác minh nhịp/cắt/âm thanh cần video; bản này chỉ chấm phần có bằng chứng.',
       'Timeline tham khảo 0–3 chi tiết gây tò mò; 3–8 mở; 8–18 dùng thử; 18–25 lợi ích; 25–30 CTA. Giải thích mỗi cut phục vụ thông tin nào. Không cho điểm âm thanh dựa vào ảnh chụp timeline.'),
      example('Bán hàng','Xử lý “đắt quá” bằng chẩn đoán và đề xuất',
       'Viết hội thoại 12 lượt, xác định 3 nhu cầu và chốt được một bước tiếp theo hợp lý.',
       'Brief GIẢ LẬP: cùng lớp 4 buổi/800.000đ, nhóm 6. Khách có ngân sách 600.000đ, chỉ rảnh tối thứ Ba, lo không theo kịp. Lịch thật trong đề: thứ Ba 19h, thứ Bảy 8h. Buổi trải nghiệm 100.000đ; không có giảm giá khác.',
       '0–10 lập 5 câu hỏi khám phá; 10–30 viết 12 lượt gồm ít nhất 3 phản đối; 30–45 đưa 2 phương án không bịa ưu đãi; 45–55 viết tin follow-up 80–120 từ; 55–60 đánh dấu câu ép mua và sửa. Phải kiểm tra ngân sách/giờ học trước khi đề xuất.',
       'DOCX: 5 câu hỏi, hội thoại 12 lượt, 2 phương án, follow-up, 3 dấu hiệu cần ngừng thúc ép. Không cần nhắn khách thật.',
       'Hướng đáp: hỏi mục tiêu và thời gian, làm rõ chênh lệch ngân sách, đưa lựa chọn trải nghiệm hoặc chờ ngân sách phù hợp. Chốt: “Bạn muốn thử tối thứ Ba hay nhận lịch để cân nhắc?” Không hứa chắc theo kịp hay tự tạo gói 600.000đ.'),
      example('Dạy','Micro-lesson 15 phút: percentage points vs percent',
       'Người học phân biệt được mức giảm tương đối và thay đổi điểm phần trăm qua 4 câu kiểm tra.',
       'Dữ liệu GIẢ LẬP: tỷ lệ dùng xe ô tô giảm 55% xuống 35%; đi xe đạp tăng 10% lên 20%. Người học biết phần trăm nhưng nhầm hai khái niệm. Có giấy/bút hoặc slide tùy chọn.',
       '0–10 xác định mục tiêu; 10–30 viết giáo án 15 phút: mở 2, giải thích 4, hướng dẫn 4, tự làm 3, exit ticket 2; 30–45 tạo 4 câu với đáp án; 45–55 tập giảng; 55–60 thiết kế phản hồi khi sai. Có câu hỏi kiểm tra sau mỗi ví dụ, không chỉ đọc định nghĩa.',
       'DOCX: giáo án theo phút, lời giải 2 ví dụ, 4 câu kiểm tra/đáp án, 2 phương án sửa hiểu nhầm, ảnh học liệu nếu có.',
       '55→35 giảm 20 điểm phần trăm, giảm tương đối 20/55≈36,36%. 10→20 tăng 10 điểm phần trăm, tăng tương đối 100%. Câu kiểm tra: 40→50 (+10pp/+25%); 80→60 (−20pp/−25%); 5→10 (+5pp/+100%); 25→20 (−5pp/−20%).'),
      example('Quay 100 source','Thư viện 100 clip: một đồ vật, mười nhóm góc',
       'Tạo 100 clip gốc 3–5 giây có định danh và contact sheet để kiểm kê; không đếm file sao chép là clip mới.',
       'Điện thoại, một đồ vật, cửa sổ sáng, mặt bàn sạch. Shotlist đầy đủ:\n'+'\n'.join(shots),
       '0–5 chuẩn bị ánh sáng/vệ sinh lens; 5–45 quay 100 clip theo shotlist (bình quân 24 giây/clip gồm thao tác); 45–55 chọn frame đại diện và lập contact sheet 10×10; 55–60 ghi log thiếu/lỗi. Mỗi clip một góc hoặc hành động khác; không quay người khác khi chưa được phép. Nếu không hoàn thành, ghi đúng số còn thiếu.',
       'DOCX: contact sheet 100 ô đọc được mã (chia nhiều trang nếu cần), bảng 001–100 với tên file/thời lượng/nhóm/tình trạng, 5 lỗi và cách sửa. File video gốc giữ tại máy; ảnh/log chưa đủ xác minh chuyển động hoặc đủ 100 clip thực.',
       'Đạt phần kiểm kê khi đủ 100 ID, khớp log, có 10 nhóm; contact sheet đánh giá bố cục/ánh sáng nhìn thấy. Chưa xem nguồn thì phải ghi “chưa xác minh clip gốc”, không chấm giả chất lượng chuyển động.'),
      example('Tạo dịch vụ gói gọn','Đóng gói dịch vụ 8 video ngắn cho cửa hàng',
       'Tạo một gói có phạm vi, giá tính được, giới hạn sửa và tiêu chí bàn giao cụ thể.',
       'Dữ liệu GIẢ LẬP: 8 video 20–30 giây; khách cung cấp source; 2 giờ nhận brief, 8 giờ dựng, 2 giờ sửa, 1 giờ bàn giao; chi phí giờ 120.000đ; chi phí khác 240.000đ. Công suất 2 gói/tuần. Không gồm quay, chạy quảng cáo hoặc bảo đảm doanh thu.',
       '0–10 xác định khách phù hợp; 10–25 viết phạm vi và quy trình 5 bước; 25–40 tính chi phí, giá với biên lợi nhuận gộp 40%; 40–50 viết giới hạn 1 vòng sửa và nghiệm thu; 50–60 soạn offer 150–200 từ + 3 câu khảo sát trước mua. Biên 40% nghĩa là giá=chi phí/(1−0,40).',
       'DOCX: chân dung khách, scope bao gồm/không gồm, quy trình/timeline 7 ngày, bảng chi phí và giá, điều kiện sửa/phát sinh, checklist bàn giao, offer.',
       'Tổng 13 giờ ×120.000 +240.000 =1.800.000đ; giá để biên gộp 40%=3.000.000đ. Không nhầm cộng 40% ra 2.520.000đ. Nghiệm thu: 8 file dọc H.264 1080×1920 đúng độ dài, phụ đề/brand đúng brief; không ràng buộc bằng số view hay doanh thu.'),
      example('Livestream','Live 20 phút: “Máy tính bị đổ oan” — vui nhưng học được điều thật',
       'Thiết kế và diễn thử một live có 1 yếu tố giữ chân chủ lực và 1 yếu tố chuyên môn chủ lực; người thích vui được tham gia, người giỏi có bài kiểm chứng đủ chiều sâu.',
       'Chủ đề: phân biệt percent và percentage points khi đọc IELTS Task 1. Dữ liệu thực hành: ô tô 55%→35%, xe đạp 10%→20%, kiểm tra chuyển giao 40%→50% và 80%→60%. Giữ chân CHỦ LỰC: trò “Bắt lỗi máy tính” — bình chọn đúng/sai và giữ lời hứa mở lời giải sau 3 phút. Chuyên môn CHỦ LỰC: phân biệt thay đổi tuyệt đối và tương đối bằng công thức + 1 ví dụ + 1 câu chuyển giao. Đạo cụ: giấy, bút, bảng số trên; điện thoại quay thử, không cần live công khai.',
       'Khung 60 phút: 0–10 chuẩn bị bảng và lời mở; 10–25 viết kịch bản; 25–45 live thử 20 phút; 45–55 xem lại; 55–60 ghi 3 sửa đổi. Timeline live: phút 0–2 mở câu đố “55→35 là giảm 20% đúng hay sai?”; 2–5 đọc bình luận, hài hước với lỗi của chính mình và mở lời giải đúng hẹn; 5–10 chứng minh công thức; 10–14 cho người giỏi giải 40→50 và phản biện; 14–18 cho người mới chọn cách diễn đạt đúng rồi giải thích; 18–20 tóm tắt và CTA lưu bảng. Chỉ một trò giữ chân xuyên suốt, không chèn hài tách rời bài học. Người đúng được mời giải thích; không chê người sai. Mỗi đoạn viết đủ lời dẫn, câu hỏi, câu nối và cách xử lý không có bình luận.',
       'DOCX: hai yếu tố chủ lực được đặt tên, bảng kịch bản 6 đoạn đủ phút và lời thoại, 4 câu hỏi/đáp án, 3 ví dụ câu nối, checklist diễn thử, log người xem theo phút nếu live thật. Nếu diễn thử một mình, ghi rõ chưa có dữ liệu giữ chân thực tế. Đính kèm frame/timecode; ảnh không chứng minh chất lượng giọng nói hay mức giữ chân.',
       '''KỊCH BẢN MẪU ĐẦY ĐỦ THEO TỪNG ĐOẠN
0–2: “Tối nay chúng ta bắt một lỗi mà tôi từng đổ oan cho máy tính. 55 xuống 35, tôi nói ‘giảm 20%’. Bạn chọn 1: đúng, hay 2: sai? Trong đúng ba phút, tôi sẽ chỉ ra phần khiến cả tôi lẫn máy tính mang tiếng. Nếu bạn đã biết, đừng chỉ chọn đáp án: hãy đoán vì sao người mới rất dễ nhầm.” Nếu không có bình luận: “Tôi giữ cả hai lựa chọn trên bảng để bạn vẫn làm được khi xem lại.”
2–5: “Tôi thấy có hai đội. Đội nào cũng có lý do; chúng ta kiểm chứng bằng mẫu số, không bằng số người bình chọn. Lỗi hài nằm ở việc tôi coi dấu % như trang trí: bỏ vào đâu cũng tưởng đúng. Máy tính hôm nay được minh oan.” Mở đúng hẹn: “55−35=20 điểm phần trăm. Nhưng 20/55≈36,36%, nên giảm tương đối khoảng 36,36%.” Nối: “Trò đố chỉ là cửa vào; giờ mình làm rõ cơ chế để bạn dùng được với bất kỳ bảng nào.”
5–10: Viết hai dòng: “Thay đổi điểm phần trăm = tỷ lệ sau − tỷ lệ trước. Thay đổi tương đối = (sau − trước)/trước ×100%.” Đọc ví dụ xe đạp 10→20: “+10 điểm phần trăm; +100% tương đối, tức là gấp đôi.” Dừng 20 giây để người xem thử diễn đạt bằng tiếng Anh: “The share of cyclists doubled from 10% to 20%.” Giải thích không suy ra số người khi chưa biết quy mô dân số. Nối: “Nếu công thức đúng, nó phải sống sót qua câu mới.”
10–14: “Người đã nắm bài: 40→50 thay đổi bao nhiêu? Cho tôi cả hai đáp án và mẫu số.” Đáp: +10 điểm phần trăm; +25% tương đối. “Nếu bạn chọn +10%, hãy thử xem 10% của 40 có phải 10 không: chỉ là 4.” Cho người giỏi phản biện trường hợp gốc bằng 0: công thức tương đối không xác định, không chia cho 0. Không coi công thức nào cũng dùng được. Nối: “Đó là tầng dành cho người muốn kiểm chứng; mình quay lại một câu đơn giản để ai cũng mang được điều gì về.”
14–18: “80→60: chọn ‘fell by 20 percentage points’ hay ‘fell by 20%’? Câu thứ nhất đúng; tương đối giảm 25%.” Mời một lời giải ngắn; nếu không có bình luận, dùng tạm hai đáp án giả định và ghi rõ là ví dụ minh họa. Quay lại trò bắt lỗi máy tính: chính cách nhập mẫu số quyết định kết quả. Hài hước phục vụ hiểu bài, không kéo dài để né lời giải.
18–20: “Tối nay máy tính hết bị oan, còn chúng ta có hai công cụ: chênh lệch đơn vị tỷ lệ và thay đổi so với ban đầu. Lưu bốn ví dụ này, thử nói một câu bằng tiếng Anh, rồi kiểm tra mẫu số. Nếu bạn đã giỏi, để lại một trường hợp dễ làm người mới nhầm; buổi sau chúng ta kiểm chứng.” Không hứa chắc tăng band hoặc giữ mọi người đến cuối.
ĐÁP ÁN 4 CÂU: 55→35: −20pp, −36,36%; 10→20: +10pp, +100%; 40→50: +10pp, +25%; 80→60: −20pp, −25%.
ĐO THỰC TẾ: chỉ nhập viewers ở các mốc 2/5/10/14/18/20 phút và average watch time khi nền tảng có cung cấp. Viewers đồng thời chịu ảnh hưởng người vào mới, không được gọi là tỷ lệ giữ chân của cùng một cohort. Muốn retention thật cần dữ liệu cohort của nền tảng. Khi chưa live, chỉ có giả thuyết: mở lời giải đúng hẹn và có bài chuyển giao sẽ tăng lý do ở lại. Không bịa tỷ lệ hay số người xem.''')]
    from .livestream import sample_plans
    expertise,retention=sample_plans()
    live=data[-1]
    live['expertise_element']='Phân biệt thay đổi tuyệt đối và tương đối bằng công thức, ví dụ và bài chuyển giao.'
    live['retention_element']='Trò Bắt lỗi máy tính với bình chọn và lời hứa mở lời giải đúng hẹn, xuyên suốt buổi live.'
    live['livestream_expertise']=expertise
    live['livestream_retention']=retention
    live['instructions']='Khung 60 phút: 0–10 chuẩn bị bảng và lời mở; 10–25 viết hai bảng kịch bản; 25–45 diễn thử 20 phút theo các mốc trong hai bảng; 45–55 xem lại; 55–60 ghi ba sửa đổi. Ghép hai bảng tại cùng mốc thời gian để lời dẫn giữ chân đưa người xem vào nội dung chuyên môn. Chỉ một trò giữ chân xuyên suốt; không chèn hài tách rời bài học. Người đúng được mời giải thích; không chê người sai.'
    live['deliverables']='DOCX: hai bảng riêng CHUYÊN MÔN và GIỮ CHÂN, mỗi bảng đủ sáu mốc thời gian, lời thoại và cách kiểm tra; đặt tên hai yếu tố chủ lực; bốn câu hỏi/đáp án; ba câu nối; checklist diễn thử và ba sửa đổi. Nếu live thật, kèm log người xem theo phút và frame/timecode. Diễn thử một mình phải ghi chưa có dữ liệu giữ chân thực tế. Ảnh không chứng minh chất lượng giọng nói hay mức giữ chân.'
    from .speaking import speaking_sample
    data.insert(1,speaking_sample())
    return add_solutions(data)
