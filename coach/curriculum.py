import json
import math
import re
from .charts import validate_chart

BATCH_SIZE=12
SCHEDULE = [
    ('IELTS','Writing'),('IELTS','Speaking'),('Cầu lông',''),('Content','Short-form'),
    ('Edit',''),('Bán hàng',''),('Dạy',''),('Quay 100 source',''),
    ('Tạo dịch vụ gói gọn',''),('Livestream','Giữ chân + chuyên môn'),('IELTS','Writing'),('IELTS','Speaking'),
    ('IELTS','Writing'),('IELTS','Speaking'),('Cầu lông',''),('Content','Storytelling'),
    ('Edit',''),('Bán hàng',''),('Dạy',''),('Quay 100 source',''),
    ('Tạo dịch vụ gói gọn',''),('Livestream','Hài hước + chuyên môn'),('IELTS','Writing'),('IELTS','Speaking')]

RUBRICS = {
    'IELTS': [('Task achievement / response',25),('Coherence & cohesion',25),('Lexical resource',25),('Grammar range & accuracy',25)],
    'Cầu lông':[('Kỹ thuật có bằng chứng',30),('Độ ổn định & kết quả',25),('Di chuyển / lựa chọn chiến thuật',25),('Tự phân tích & điều chỉnh',20)],
    'Content':[('Insight & giá trị',30),('Cấu trúc / giữ chú ý',25),('Giọng viết & diễn đạt',25),('CTA & kế hoạch đo',20)],
    'Edit':[('Nhịp & mạch câu chuyện',30),('Âm thanh / chữ / màu',25),('Tính nhất quán',25),('Xuất bản & tự kiểm',20)],
    'Bán hàng':[('Chẩn đoán nhu cầu',30),('Đề xuất giá trị',25),('Xử lý phản đối',25),('Chốt bước tiếp theo',20)],
    'Dạy':[('Mục tiêu & thiết kế',30),('Giải thích / minh họa',25),('Kiểm tra hiểu biết',25),('Phản hồi & điều chỉnh',20)],
    'Quay 100 source':[('Đủ 100 shot có định danh',30),('Bố cục / ánh sáng',25),('Đa dạng / tính sử dụng',25),('Quản lý nguồn & tự kiểm',20)],
    'Tạo dịch vụ gói gọn':[('Khách hàng & lời hứa',30),('Phạm vi / quy trình',25),('Chi phí & giá minh bạch',25),('Bàn giao / kiểm nghiệm',20)],
    'Livestream':[('Giữ chân & tương tác',35),('Giá trị chuyên môn & độ chính xác',35),('Mạch dẫn & chuyển đoạn',20),('Đo lường & tự phản hồi',10)]}


def rubric_for(category,skill):
    if category=='IELTS' and skill in ('Reading','Listening'):
        return [{'name':'Độ chính xác 40 câu','max_score':100}]
    if category=='IELTS' and skill=='Speaking':
        return [{'name':n,'max_score':25} for n in ['Fluency & coherence','Lexical resource','Grammar range & accuracy','Pronunciation']]
    return [{'name':n,'max_score':v} for n,v in RUBRICS[category]]


def parse_json(answer):
    text = answer.strip()
    text = re.sub(r'^```(?:json)?\s*','',text,flags=re.I)
    text = re.sub(r'\s*```$','',text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find('{')
        if start < 0:
            raise ValueError('Codex chưa xuất JSON hợp lệ.')
        value,end = json.JSONDecoder().raw_decode(text[start:])
        if not isinstance(value,dict):
            raise ValueError('Kết quả AI phải là một đối tượng JSON.')
        return value


def validate_assignment(data, category, skill):
    if not isinstance(data,dict):
        raise ValueError('Đề phải là JSON object.')
    for name in ['title','objective','materials','instructions','deliverables','answer_key']:
        if not isinstance(data.get(name),str) or len(data[name].strip())<8:
            raise ValueError('Đề chưa đầy đủ: '+name)
    if skill not in ('Reading','Listening') and len(data['answer_key'].split())<200:
        raise ValueError('Đáp án/bài mẫu còn quá ngắn; cần full đầu ra, không chỉ gợi ý.')
    rubric = rubric_for(category,skill)
    if data.get('rubric') != rubric:
        raise ValueError('Rubric AI không khớp chuẩn chấm cố định.')
    if data.get('duration_minutes') != 60:
        raise ValueError('Đề cần đúng khung 60 phút.')
    if category=='IELTS' and skill in ('Reading','Listening'):
        q = data.get('questions')
        if not isinstance(q,list) or len(q)!=40:
            raise ValueError('Listening/Reading cần đủ 40 câu.')
        for i, item in enumerate(q,1):
            if not isinstance(item,dict) or item.get('number')!=i or not isinstance(item.get('question'),str) or not item['question'].strip() or not isinstance(item.get('answer'),str) or not item['answer'].strip() or not item.get('explanation'):
                raise ValueError('Câu hỏi / đáp án / giải thích chưa đầy đủ.')
    if category=='IELTS' and skill=='Listening':
        sections=data.get('listening_sections')
        if not isinstance(sections,list) or len(sections)!=4 or any(not isinstance(s,str) or len(s)<300 for s in sections):
            raise ValueError('Listening cần bốn transcript để tạo audio thực.')
        if any(len(s.split())<350 for s in sections):
            raise ValueError('Transcript Listening quá ngắn; cần bốn section đầy đủ.')
    if category=='IELTS' and skill=='Reading':
        passages=data.get('reading_passages',[])
        if len(passages)!=3 or any(not isinstance(s,str) or len(s.split())<500 for s in passages):
            raise ValueError('Reading cần ba passage đầy đủ, không rút gọn.')
    if category=='Quay 100 source':
        listed=set(int(m) for m in re.findall(r'(?m)^\s*(\d{1,3})[.\s|:)]',data['materials']))
        if not set(range(1,101)).issubset(listed):
            raise ValueError('Shotlist phải có đủ 100 dòng đánh số 001–100.')
    if category=='IELTS' and skill=='Writing':
        validate_chart(data.get('chart'))
        if not isinstance(data.get('writing_tasks'),list) or len(data['writing_tasks'])!=2 or any(not isinstance(v,str) or len(v)<60 for v in data['writing_tasks']):
            raise ValueError('Writing cần Task 1 có dữ liệu và Task 2 đầy đủ.')
    if category=='IELTS' and skill=='Speaking':
        tasks=data.get('speaking_tasks')
        if not isinstance(tasks,dict) or any(not isinstance(tasks.get(k),dict) for k in ('part1','part2','part3')):
            raise ValueError('Speaking cần đầy đủ Part 1, cue card Part 2 và Part 3.')
        for key,minimum in [('part1',8),('part3',6)]:
            questions=tasks[key].get('questions')
            if not isinstance(questions,list) or len(questions)<minimum or any(not isinstance(q,str) or len(q.strip())<10 for q in questions):
                raise ValueError('Speaking '+key+' chưa có đủ câu hỏi cụ thể.')
        p2=tasks['part2']
        if not isinstance(p2.get('cue_card'),str) or len(p2['cue_card'].strip())<20:
            raise ValueError('Speaking Part 2 thiếu cue card.')
        for key,minimum in [('bullets',4),('followups',2)]:
            if not isinstance(p2.get(key),list) or len(p2[key])<minimum or any(not isinstance(q,str) or not q.strip() for q in p2[key]):
                raise ValueError('Speaking Part 2 cần bốn gợi ý và hai câu hỏi tiếp nối.')
        from .speaking import speaking_parts
        data['speaking_parts']=speaking_parts(tasks)
    if category=='Livestream':
        for key in ('retention_element','expertise_element'):
            if not isinstance(data.get(key),str) or len(data[key])<30:
                raise ValueError('Livestream cần nêu riêng yếu tố giữ chân và yếu tố chuyên môn.')
        for key in ('livestream_expertise','livestream_retention'):
            rows=data.get(key)
            if not isinstance(rows,list) or len(rows)<6:
                raise ValueError('Livestream cần hai bảng riêng chuyên môn và giữ chân, mỗi bảng ít nhất sáu đoạn.')
            if any(not isinstance(row,dict) or any(not isinstance(row.get(field),str) or not row[field].strip() for field in ('time','focus','script','check')) for row in rows):
                raise ValueError('Mỗi dòng bảng Livestream cần mốc phút, mục tiêu, lời dẫn và cách kiểm tra.')
        if [r['time'] for r in data['livestream_expertise']] != [r['time'] for r in data['livestream_retention']]:
            raise ValueError('Hai bảng Livestream cần cùng mốc thời gian để dễ đối chiếu.')
    return data


def assignment_prompt(category,skill,level,band,goal,recent):
    schema={'title':'','objective':'','duration_minutes':60,'materials':'','instructions':'',
            'deliverables':'','rubric':rubric_for(category,skill),'answer_key':''}
    extra=''
    if category=='IELTS':
        extra=f'IELTS Academic, trình độ {band}, mục tiêu {goal}. Đề bằng tiếng Anh, hướng dẫn nộp bằng tiếng Việt. Đây là bài luyện, không phải kỳ thi chứng nhận band.'
        if skill in ('Reading','Listening'):
            schema['questions']=[{'number':1,'question':'','answer':'','explanation':''}]
            extra+=' BẮT BUỘC 40 câu liên tiếp 1–40, đầy đủ lời giải từng câu, không dùng dấu ... hoặc placeholder. questions chứa đáp án chỉ để máy chấm, materials/instructions KHÔNG lộ đáp án. Reading: ba passage tự viết 600–800 từ mỗi passage; đa dạng loại câu, rõ word limit. Listening: bốn section, mỗi section 10 câu; transcript tự viết 450–650 từ/section, giọng TTS sẽ đọc, đánh dấu người nói bằng tên; hướng dẫn nghe hai lượt trong khung 60 phút. Không đưa transcript vào materials.'
        if skill=='Listening':
            schema['listening_sections']=['transcript 1','transcript 2','transcript 3','transcript 4']
        if skill=='Reading':
            schema['reading_passages']=['Passage 1','Passage 2','Passage 3']
            extra+=' Chứa ba passage trong reading_passages, không lặp chúng trong materials. Mỗi passage ít nhất 500 từ; materials chỉ ghi dữ liệu/hướng dẫn chung.'
        if skill=='Writing':
            schema['chart']={'type':'bar','title':'English chart title','unit':'%',
                'categories':['A','B'],'series':[{'name':'Year 1','values':[60,40]},{'name':'Year 2','values':[45,55]}],
                'source_note':'Practice dataset created for this exercise, not official statistics.'}
            schema['writing_tasks']=['Task 1: dữ liệu bảng/biểu đồ, ít nhất 150 từ, 20 phút','Task 2: câu hỏi nghị luận ít nhất 250 từ, 40 phút']
            extra+=' Task 1 phải có chart object (bar hoặc line) với đầy đủ số liệu; ứng dụng vẽ biểu đồ PNG THẬT từ chart. materials chứa bảng dữ liệu KHỚP CHÍNH XÁC chart; title/labels bằng tiếng Anh, đơn vị rõ, 2–10 categories, 1–4 series, mỗi series.values có đủ số theo categories. Nếu là cơ cấu %, tổng mỗi năm 100%. Ghi rõ dữ liệu thực hành tự tạo. Task 2 có câu hỏi cụ thể. answer_key có cả hai bài mẫu đủ 150/250 từ kèm phân tích. Chấm Task 2 trọng số gấp đôi Task 1.'
        if skill=='Speaking':
            schema['speaking_tasks']={'part1':{'questions':['eight complete questions']},'part2':{'cue_card':'Describe ...','bullets':['four specific bullet points'],'followups':['two complete follow-up questions']},'part3':{'questions':['six complete discussion questions']}}
            extra+=' FULL SPEAKING: Part 1 ít nhất 8 câu cụ thể về 2–3 chủ đề quen thuộc (4–5 phút); Part 2 cue_card cụ thể, bullets đủ 4 gợi ý, chuẩn bị 1 phút/nói tối đa 2 phút, followups đủ 2 câu ngắn (cả phần 3–4 phút); Part 3 ít nhất 6 câu thảo luận sâu liên quan cue card (4–5 phút). Tổng lượt diễn thử 11–14 phút trong khung luyện 60 phút. answer_key phải trả lời TỪNG câu Part 1, bài nói Part 2 khoảng 230–280 từ, hai followups và TỪNG câu Part 3; không chỉ đưa outline hay từ vựng. Có giải thích cách phát triển ý và lỗi thường gặp, không hứa band. Yêu cầu nộp voice/audio + transcript nếu có. Không hứa chấm phát âm từ transcript; phần phát âm cần người nghe thực tế xác minh.'
    if category=='Quay 100 source':
        extra+=' 100 source nghĩa là 100 clip gốc khác nhau 3–5 giây, quay bằng điện thoại. Cung cấp SHOTLIST ĐỦ 100 dòng đánh số 001–100, không rút gọn; 10 nhóm bối cảnh, cách quay, tên file, checklist; gói đầu ra là contact sheet 100 ô + bảng log. Không giả định đã xem video từ ảnh tĩnh.'
    if category=='Cầu lông':
        extra+=' Bài thực hành có khởi động, nghỉ, số set/lần và bảng ghi; không hứa xác minh động tác qua ảnh. Dừng nếu đau, bài nhẹ, có biến thể tại nhà; yêu cầu chuỗi ảnh rõ và log nếu chỉ nộp DOCX.'
    if category=='Livestream':
        schema['retention_element']='Một yếu tố giữ chân chủ lực và cách dùng xuyên suốt buổi live'
        schema['expertise_element']='Một yếu tố chuyên môn chủ lực kèm cơ chế, bằng chứng và bài chuyển giao'
        schema['livestream_expertise']=[{'time':'0–2','focus':'Mục tiêu chuyên môn','script':'Lời dẫn / câu hỏi cụ thể','check':'Cách kiểm tra hiểu biết'}]
        schema['livestream_retention']=[{'time':'0–2','focus':'Hoạt động giữ chân','script':'Lời dẫn, câu nối và phương án khi không có bình luận','check':'Dấu hiệu theo dõi; ghi rõ chưa có số liệu nếu chỉ diễn thử'}]
        extra+=' Trình bày kế hoạch thành HAI BẢNG RIÊNG: livestream_expertise và livestream_retention, ít nhất sáu dòng mỗi bảng, CÙNG mốc time và bao phủ live 20 phút. Mỗi dòng đủ focus/script/check. Hai bảng mô tả nhiệm vụ của người học, không làm lộ lời giải câu hỏi; giữ lời giải trong answer_key. instructions chỉ ghi quy trình chuẩn bị/diễn thử/tự đánh giá trong 60 phút. deliverables yêu cầu người học nộp hai bảng tương ứng.'
        extra+=' Một bài livestream BẮT BUỘC có đúng 1 yếu tố giữ chân chủ lực (tương tác/hài hước có chủ đích, không làm nhục người xem) và 1 yếu tố chuyên môn chủ lực (bằng chứng, giải thích cơ chế, thực hành có kiểm tra). Hai yếu tố phải nối mượt để người giỏi chuyên môn lẫn người thích hài hước đều có lý do ở lại. Chọn chủ đề cụ thể; cung cấp toàn bộ brief/dữ liệu. Kịch bản 20 phút đủ từng đoạn, lời dẫn mẫu và timeline; chu kỳ setup/thực hành/tự đánh giá tổng 60 phút. Có cách tiếp nhận bình luận và thước đo giữ chân dự kiến (watch time, viewers theo phút) mà không bịa số liệu thực tế hoặc cam kết chắc chắn giữ được người xem. answer_key chứa kịch bản mẫu trọn vẹn và giải thích vị trí hai yếu tố.'
    return f'''Bạn là người thiết kế bài thực hành đầy đủ, có thể thực hiện ngay trong 60 phút.
Nhóm: {category}; kỹ năng: {skill}; hệ số độ khó: {level:.2f}.
{extra}
Tránh lặp lại các tiêu đề: {json.dumps(recent,ensure_ascii=False)}.
Tăng độ khó bằng độ phức tạp, độ chính xác, ràng buộc; KHÔNG tăng thời lượng. Dữ liệu giả lập phải ghi rõ là dữ liệu thực hành. Tất cả nguyên liệu phải nằm trong đề; không phụ thuộc link, công cụ trả tiền hoặc yêu cầu người học tự tìm đề. Ghi rõ mục tiêu đo được, bước làm, phân bổ 60 phút, đầu ra và tiêu chí cho đủ 100 điểm. Rubric dùng đúng schema, không thay đổi tên/điểm.
answer_key: lời giải đầy đủ, bài mẫu cụ thể và lỗi thường gặp; phải tách khỏi đề công khai. Không tự ghi điểm năng lực của người học. Mỗi giờ app phát một BỘ đủ 12 đề: 8 nhóm khác + 2 Writing + 2 Speaking, không có Listening/Reading. Người học lưu bài ở ô cuối từng đề, hoàn thành đủ 12 bài của cùng bộ mới gửi đi chấm. App chấm nền và trả kết quả cả bộ cùng lúc. Hai Writing và hai Speaking phải có chủ đề khác nhau.
Xuất duy nhất đối tượng JSON hợp lệ theo schema sau; không markdown ngoài JSON, không lời chào, không rút gọn bất kỳ phần nào:
{json.dumps(schema,ensure_ascii=False)}'''


def public_assignment(data):
    public={k:v for k,v in data.items() if k not in ('answer_key','listening_sections','writing_model_answers')}
    if 'questions' in public:
        public['questions']=[{'number':q['number'],'question':q['question']} for q in public['questions']]
    return public


def assignment_text(task):
    data = public_assignment(json.loads(task['body']))
    lines=[f"{task['id']} · {task['category']} {task['skill']}",data['title'],
           '\nMỤC TIÊU\n'+data['objective'],'\nDỮ LIỆU / NGUYÊN LIỆU\n'+data['materials'],
           '\nYÊU CẦU & 60 PHÚT\n'+data['instructions']]
    for key,label in [('writing_tasks','WRITING'),('speaking_parts','SPEAKING')]:
        if data.get(key):
            lines.append('\n'+label+'\n'+'\n\n'.join(data[key]))
    if data.get('reading_passages'):
        lines.append('\nREADING PASSAGES\n'+'\n\n'.join(data['reading_passages']))
    if data.get('questions'):
        lines.append('\nCÂU HỎI\n'+'\n'.join(f"{q['number']}. {q['question']}" for q in data['questions']))
    for key,label in [('livestream_expertise','BẢNG CHUYÊN MÔN'),('livestream_retention','BẢNG GIỮ CHÂN')]:
        if data.get(key):
            lines.append('\n'+label+'\n'+'\n\n'.join(f"{r['time']} phút · {r['focus']}\n{r['script']}\nKiểm tra: {r['check']}" for r in data[key]))
    lines.extend(['\nNỘP BÀI\n'+data['deliverables'], '\nTHANG CHẤM\n'+'\n'.join(f"{r['name']}: {r['max_score']} điểm" for r in data['rubric']),
       f"\nMở Hourly Coach trên laptop → Bộ bài & chấm → {task['id']}. Lưu text/ảnh/video/DOCX/audio ngay cuối đề và đánh dấu hoàn thành. Đủ 12 bài cùng bộ (8 nhóm khác + 2 Writing + 2 Speaking) → Gửi tất cả & chấm; kết quả mở cùng lúc. Bộ tiếp theo có tại mốc giờ đúng; bộ cũ vẫn làm được. FULL ĐÁP ÁN nằm ở tab Đáp án, có thể mở khi bí. Khai rõ có/không tham khảo đáp án."])
    return '\n'.join(lines)


def validate_evaluation(data,rubric):
    if not isinstance(data,dict):
        raise ValueError('Đánh giá chưa phải JSON object.')
    items=data.get('criteria')
    if not isinstance(items,list) or len(items)!=len(rubric):
        raise ValueError('Đánh giá chưa đủ tiêu chí.')
    total=0
    complete=True
    for expected,item in zip(rubric,items):
        if item.get('name')!=expected['name'] or item.get('max_score')!=expected['max_score']:
            raise ValueError('AI đã thay đổi thang chấm.')
        score=item.get('score')
        if score is None:
            complete=False
        elif isinstance(score,bool) or not isinstance(score,(int,float)) or not math.isfinite(score) or not 0<=score<=expected['max_score']:
            raise ValueError('Điểm ngoài thang chấm.')
        else:
            total+=score
        if not isinstance(item.get('feedback'),str) or not item['feedback'].strip():
            raise ValueError('Chưa có giải thích cho từng tiêu chí.')
    for key in ('summary','corrections','model_answer','next_steps','evidence_limits'):
        if not isinstance(data.get(key),str) or not data[key].strip():
            raise ValueError('Đánh giá thiếu '+key)
    # Derive the total instead of trusting AI arithmetic. Incomplete evidence never counts as mastery.
    data['score']=round(total,1) if complete else None
    data['observed_points']=round(total,1)
    data['complete']=complete
    return data
