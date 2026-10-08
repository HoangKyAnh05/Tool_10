"""Original Codex-authored practice bank. Sources describe formats, not copied questions.

The starter bank is authored in this Codex chat. Hourly bundles use the configured
gateway separately. Both are checked for full content and duplicate questions.
"""
import json,time
from .curriculum import SCHEDULE,validate_assignment,rubric_for
from .lessons import create_set,save_exercise,prepare_assets,publish_set
from .novelty import validate_novelty,fingerprint

IELTS_SOURCE='https://ielts.org/take-a-test/preparation-resources/sample-test-questions/academic-test'
SOURCE='Codex biên soạn · ngân hàng luyện trước · không phải đề thi chính thức'

# Each context is a different client brief, audience, product and constraint.
CONTEXTS=[
 ('Góc Yên','quán cà phê học tập','sinh viên ôn thi','chỗ ngồi yên tĩnh hai giờ','ồn vào giờ cao điểm',49000,'video kể chuyện một lần mất tập trung'),
 ('Vợt Mới','câu lạc bộ cầu lông','người mới chơi','buổi làm quen 45 phút','ngại chơi cùng người giỏi',89000,'video hướng dẫn một lỗi cầm vợt'),
 ('Viết Rõ','lớp IELTS Writing','người học band 6.5','buổi sửa overview Task 1','nhầm percent với percentage points',129000,'carousel giải thích một lỗi số liệu'),
 ('Mặc Lại','cửa hàng đồ cũ','người mua tiết kiệm','combo ba món đã kiểm tra','lo chất lượng đồ đã sử dụng',159000,'video trước và sau phục hồi áo cũ'),
 ('Bếp Gọn','dịch vụ chuẩn bị bữa ăn','người đi làm bận rộn','gói ba bữa đặt trước','không biết thành phần và khẩu phần',189000,'video POV đóng hộp một đơn hàng'),
 ('Mầm Nhỏ','góc cây ban công','người ở căn hộ','bộ chăm cây bảy ngày','hay tưới quá nhiều nước',99000,'bài viết phá một hiểu lầm chăm cây'),
 ('Trang Mở','câu lạc bộ đọc sách','người muốn đọc đều','buổi đọc chung có trao đổi','mua sách rồi không đọc hết',59000,'video review sách không tiết lộ kết thúc'),
 ('Khung Sáng','dịch vụ ảnh chân dung','người cần ảnh hồ sơ','buổi chụp với ba ảnh chỉnh','ngại tạo dáng trước máy ảnh',249000,'video phỏng vấn khách hàng giả lập'),
 ('Nét Đầu','lớp vẽ cho người mới','người chưa học mỹ thuật','buổi vẽ tĩnh vật một giờ','sợ mình không có năng khiếu',119000,'video thử thách sửa một bức vẽ lỗi'),
 ('Ô Rõ','lớp bảng tính','người mới đi làm','buổi làm sạch bảng dữ liệu','sợ công thức và dữ liệu lộn xộn',149000,'bài kể chuyện giải quyết một bảng lỗi'),
]

# Twenty separate essay issues, with topic-specific supporting arguments/examples.
ESSAYS=[
 ('urban public transport','Cities should make public transport free for all residents. How far do you agree?',
  'removing fares would help low-income workers travel to interviews and essential appointments',
  'a bus network still needs reliable services, accessible stops and a stable maintenance budget',
  'a night-shift worker gains little from a free bus that stops running before the shift ends'),
 ('renewable energy','Public funding for clean energy should take priority over fossil-fuel subsidies. Do you agree?',
  'investment in clean power can reduce dependence on imported fuels and support technical training',
  'families facing high heating costs need a gradual transition rather than an abrupt withdrawal of support',
  'insulating older homes can reduce demand while new electricity capacity is being built'),
 ('public libraries','Some favour digital libraries; others prefer physical branches. Discuss both positions and give your view.',
  'digital collections allow readers to borrow material outside normal opening hours',
  'physical branches provide quiet study space and help residents who lack devices or digital skills',
  'a student sharing one room with siblings may need a desk at a neighbourhood branch'),
 ('university subjects','Students should choose university subjects mainly for future earnings. Do you agree?',
  'employment prospects matter when students must repay fees and support their families',
  'interest and aptitude influence persistence, while forecasts about future salaries are uncertain',
  'a talented trainee teacher may contribute more than an unwilling graduate in a fashionable field'),
 ('local tourism','Tourism can help small towns but also create problems. What should towns do to manage this?',
  'visitor spending can support independent shops and give young residents employment options',
  'crowded streets, seasonal jobs and pressure on housing can reduce residents quality of life',
  'a town could direct coach parking outside its centre and use booking slots for popular attractions'),
 ('flexible working','Remote work benefits employees more than employers. How far do you agree?',
  'employees may save commuting time and organize uninterrupted work around their most productive hours',
  'employers can recruit beyond one city but must manage coordination, training and secure access',
  'a team can schedule shared planning sessions while keeping individual drafting work flexible'),
 ('household recycling','Who should be mainly responsible for reducing household waste: consumers or producers?',
  'consumers can separate materials and avoid unnecessary purchases when clear alternatives exist',
  'producers decide how goods are packaged and can design refillable or easier-to-repair products',
  'a refill station is useful only if containers are compatible and the return process is convenient'),
 ('internet access','Affordable internet access should be treated as an essential public service. Do you agree?',
  'reliable access supports job applications, education and contact with public services',
  'access alone does not solve exclusion when people lack devices, training or safe ways to use them',
  'a community centre can combine affordable connections with practical sessions on online forms'),
 ('community volunteering','Schools should require students to complete community volunteering. Do you agree?',
  'well-designed projects let students practice cooperation and understand local needs',
  'compulsory unpaid work may feel like punishment if tasks are irrelevant or clash with responsibilities',
  'students could choose between a library project, a park clean-up and support for a local club'),
 ('sports participation','Should towns invest more in elite sporting events or everyday facilities? Discuss both views.',
  'elite events can inspire participation and bring temporary business to a host town',
  'accessible everyday facilities provide repeated opportunities to exercise across age groups',
  'a modest public court with affordable booking may serve more residents than a rarely used stadium'),
 ('urban green space','Growing cities should protect parks even when more housing is needed. Do you agree?',
  'parks provide shared places to relax, exercise and meet without purchasing anything',
  'housing shortages also harm residents and require efficient use of land near existing services',
  'building compact homes near transit can ease demand without removing the only local playground'),
 ('arts education','Arts subjects are as important as science subjects at school. Discuss your opinion.',
  'arts activities develop expression, interpretation and the confidence to revise unfinished work',
  'scientific knowledge supports informed decisions, and schools have limited time for all subjects',
  'a project involving stage lighting can combine visual design with a practical explanation of electricity'),
 ('food packaging','Should governments restrict single-use food packaging? Explain your view.',
  'restrictions can reduce avoidable material waste and encourage convenient reusable alternatives',
  'food safety, accessibility and the resources used to wash alternatives must also be considered',
  'a lunch service could test returnable boxes with a deposit before expanding the scheme'),
 ('online learning','Online courses will eventually replace classroom teaching. How far do you agree?',
  'online courses make repeated explanations and flexible study available to more learners',
  'hands-on practice, immediate feedback and social interaction remain difficult to reproduce fully',
  'a beginner can watch a drawing demonstration online but may need direct help correcting a grip'),
 ('repair skills','Schools should teach students to repair everyday objects. Do you agree?',
  'basic repair encourages patience, resourcefulness and more thoughtful purchasing decisions',
  'schools need safe equipment and trained supervision, and some products are not designed for repair',
  'students could begin with a loose button or a bicycle puncture before attempting complex equipment'),
 ('historic buildings','Maintaining historic buildings is a better use of money than building new attractions. Discuss.',
  'historic places preserve local identity and can support education and visitor interest',
  'maintenance costs can be substantial, and public buildings must remain useful and accessible',
  'a former station can be adapted into a small museum with community rooms rather than left empty'),
 ('advertising to children','Advertising aimed at young children should be limited. Do you agree?',
  'young children may struggle to distinguish an entertaining message from a commercial purpose',
  'families and schools also need practical media education because advertising appears in many settings',
  'a class could compare a toy advertisement with the actual product specifications'),
 ('urban cycling','How can local authorities encourage more people to cycle for short journeys?',
  'connected routes and secure storage can make a bicycle a practical option for everyday trips',
  'training campaigns will have limited effects if routes feel unsafe or disappear at busy junctions',
  'linking a residential street to a school with a protected crossing may remove a specific barrier'),
 ('career changes','People now change careers more often. What are the advantages and disadvantages?',
  'changing careers can allow people to use neglected interests and respond to shifts in demand',
  'retraining has financial costs and uncertain outcomes, especially for people with dependants',
  'a worker might test a new field through evening classes before leaving a stable position'),
 ('screen time','Parents should set strict limits on all screen use by teenagers. How far do you agree?',
  'clear boundaries can protect sleep and make time for exercise and face-to-face relationships',
  'the purpose and quality of use matter because homework, creative work and passive scrolling differ',
  'a family can agree on device-free meals while allowing a planned video-editing project'),
]
POSITIONS=[
 'I partly agree: targeted free travel is valuable, but reliable service should take priority over removing every fare.',
 'I support prioritising clean energy while keeping temporary, targeted help for vulnerable households.',
 'I favour a combined library service: digital collections and physical branches meet different needs.',
 'Earnings matter, but they should not outweigh interests and demonstrated strengths.',
 'Towns should manage visitor transport and numbers, protect residential areas and maintain shared services.',
 'Both employees and employers can benefit from remote work if coordination and training are planned.',
 'Responsibility is shared, but producers should lead design changes that consumers cannot make alone.',
 'I agree that affordable internet is essential, together with devices, practical support and safe service design.',
 'I oppose rigid compulsory volunteering hours; schools should offer meaningful projects with choice.',
 'Elite events have value, but I would prioritise affordable facilities used regularly by local residents.',
 'Important parks should be protected while housing is expanded through compact development and better planning.',
 'Arts and sciences are both important; schools should provide a balanced foundation.',
 'I favour proportionate packaging restrictions with suitable alternatives and genuine safety exemptions.',
 'I disagree that online teaching will replace every classroom; different learners need different combinations.',
 'I support safe basic repair lessons with trained supervision.',
 'I favour adapting useful historic buildings before constructing new attractions, with individual assessment of costs.',
 'I support limits on advertising to young children alongside practical media education.',
 'Authorities should remove safety barriers through connected routes, safer junctions and secure cycle storage.',
 'Career changes can improve motivation and adaptability, but training costs and uncertainty require preparation.',
 'I support firm boundaries for sleep, but study, creative work and passive entertainment should be treated differently.',
]
CONTENT_CASES=[
 ('Kể chuyện 45 giây','Nhân vật học ở bàn gần cửa ồn, chuyển sang khu yên; không hứa tăng điểm.',
  '0–5: “Tôi mở laptop để học, rồi mười phút sau nhận ra mình đang nghe chuyện bàn bên.” 5–15: nhân vật đóng tab, viết một mục tiêu, nhưng tiếng cửa vẫn làm mất nhịp. 15–30: “Tôi thử đổi chỗ, chọn khu yên và đặt điện thoại xa tay. Không có phép màu: tôi vẫn phải làm bài, chỉ bớt một nguồn phân tâm.” 30–40: so hai góc bàn trước/sau, mô tả điều nhìn thấy. 40–45: “Cần chỗ học hai giờ? Hỏi khu ngồi, độ yên và điều kiện sử dụng trước khi chọn.”'),
 ('Tutorial 30 giây','Lỗi giả lập: siết grip liên tục; tập chậm với tay thư giãn giữa các lần chạm.',
  '0–4: “Tay mỏi nhanh khi mới chơi? Kiểm một thói quen trước khi tăng lực.” 4–12: cận hai cách cầm; “Đây là cảnh diễn lỗi siết liên tục. Thử thư giãn giữa các lần chạm.” 12–22: “Tập chậm, đưa vợt về chuẩn bị, ghi cảm giác và kết quả. Đau thì dừng.” 22–30: “Ảnh đẹp không chứng minh cả buổi đã đúng. Quay đoạn trước/sau cùng góc để người có chuyên môn xem lại.”'),
 ('Carousel 6 slide','Dữ liệu luyện: 40%→60%, 80%→60%; chênh lệch và mức thay đổi tương đối.',
  'Slide 1: “40% lên 60%: tăng 20% hay 20 points?” Slide 2: “60−40=20 percentage points.” Slide 3: “(60−40)/40×100=50% tương đối.” Slide 4: “80→60 giảm 20 points, nhưng giảm tương đối 25%.” Slide 5: “The share rose by 20 percentage points. Dùng percent tương đối thì nói rõ nền so sánh.” Slide 6: “Lưu hai công thức rồi tự thử 25→40. Không suy số người khi chưa biết tổng.”'),
 ('Before/after 30 giây','Áo giả lập có nút lỏng và nếp nhăn; sửa thật, không dùng chỉnh màu che vết.',
  '0–5: “Áo này cần bỏ hay cần kiểm?” Hiện nút lỏng và nếp vải. 5–15: quay thay nút và làm phẳng theo nhãn áo. 15–23: “Nút chắc hơn và vải gọn hơn là hai chi tiết nhìn thấy. Độ bền lâu cần thời gian kiểm.” 23–30: so ảnh cùng sáng, cùng góc; “Hỏi tình trạng, kích thước và lỗi còn lại; đừng chọn chỉ vì ảnh sau đẹp.”'),
 ('POV 40 giây','Đơn mô phỏng ba hộp; nhãn có tên món, thành phần và ngày chuẩn bị.',
  '0–5: “POV: đặt ba bữa, nhưng thông tin trên hộp quan trọng như hình món ăn.” 5–15: chia món vào hộp, kiểm tên đơn giả lập. 15–27: “Kiểm tên món, thành phần, ngày chuẩn bị và điều kiện bảo quản cần xác nhận. Có yêu cầu riêng thì hỏi thêm nguyên liệu.” 27–35: cận nhãn, che dữ liệu khách thật. 35–40: “Nhắn THÀNH PHẦN để xem mô tả trước khi quyết định.”'),
 ('Myth-busting 35 giây','Đất còn ẩm nhưng người mới muốn tưới theo lịch; quan sát trước khi thay đổi.',
  '0–5: “Ngày nào cũng tưới mới là chăm tốt? Chưa chắc.” 5–15: cận đất/chậu; “Đất còn ẩm thì tưới thêm theo lịch có thể không phù hợp; cây, chậu và điều kiện khác nhau.” 15–27: “Đọc hướng dẫn cho loại cây, kiểm đất và thoát nước, ghi quan sát trước khi thay đổi.” 27–35: “Một lá không nói hết nguyên nhân. Lưu bảng theo dõi bảy ngày, đừng thử mọi mẹo cùng lúc.”'),
 ('Review không spoil 45 giây','Sách hư cấu Một ngày chậm: người sửa ghế cũ, câu văn ngắn, chủ đề kiên nhẫn.',
  '0–5: “Sách hư cấu này hợp nếu bạn thích chuyện nhỏ hơn một cú twist.” 5–18: “Một ngày chậm kể về người sửa ghế cũ và các cuộc trò chuyện quanh nó. Tôi chú ý cách đồ vật giữ ký ức, không kể kết thúc.” 18–32: “Ưu điểm: chi tiết đời thường, câu ngắn. Hạn chế: người thích nhịp nhanh có thể thấy chậm.” 32–45: “Chọn một cảnh để trao đổi điều mình nhận ra. Đây là review minh họa, không phải sách đang bán.”'),
 ('Phỏng vấn 40 giây','Khách đóng vai và phản hồi mô phỏng phải được ghi rõ; nỗi lo tạo dáng cứng.',
  'Người hỏi: “Điều gì làm bạn ngại chụp?” Khách đóng vai: “Không biết để tay đâu, sợ cười gượng.” Người hỏi: “Bước nào giúp bạn dễ thử?” Khách: “Nói chuyện trước, thử tư thế thoải mái rồi xem ảnh kiểm.” Người hỏi: “Có cần hứa ảnh hoàn hảo cho mọi người?” Khách: “Không, tôi cần hiểu buổi chụp và cách chọn ảnh.” Kết: “Phỏng vấn mô phỏng. Hỏi phạm vi, số ảnh và vòng chỉnh trước khi đặt.”'),
 ('Challenge 45 giây','Tranh diễn lỗi: cốc nghiêng trục, hướng bóng không nhất quán; sửa hình lớn trước chi tiết.',
  '0–5: “Sửa tranh này trong ba bước, không cần biến thành kiệt tác.” 5–17: chỉ trục cốc; “Kiểm hướng trục trước nét đẹp.” 17–29: “Chọn một hướng sáng, giữ vùng tối cùng logic.” 29–38: “So hình lớn trước chi tiết, bỏ một nét thừa.” 38–45: so hai bản, ghi diễn thử; “Lưu ba sửa đổi có lý do. Đừng kết luận thiếu năng khiếu từ bản đầu.”'),
 ('Storytelling bài viết','Bảng giả lập sáu dòng, dòng 3 lặp dòng 2, dòng 5 thiếu mã; giữ bản gốc trước sửa.',
  '“Tôi từng nghĩ bảng gọn là bảng đúng. Bản mô phỏng có sáu dòng, nhưng một dòng lặp và một dòng thiếu mã. Nếu gửi ngay, tổng đẹp vẫn có thể sai. Tôi giữ bản gốc, đánh dấu dòng nghi vấn, hỏi cách định nghĩa một bản ghi duy nhất. Sau đó xử lý trùng theo mã đã xác nhận, đưa dòng thiếu vào danh sách bổ sung, kiểm lại số dòng và tổng. Bài học không phải dùng một nút cho mọi bảng: phải hiểu dữ liệu. Lưu ba bước: bản gốc, khóa nhận diện, kiểm sau sửa. Không chắc thì hỏi trước khi xóa.”'),
]
CHART_TOPICS=[
 ('Commuting modes',['Bus','Car','Bicycle','Walking']),('Sources of electricity',['Solar','Wind','Gas','Coal']),
 ('Library loans',['Fiction','History','Science','Children']),('University enrolment',['Business','Science','Arts','Education']),
 ('Visitors to a coastal town',['Day trips','Hotels','Campsites','Family visits']),('Working arrangements',['Office','Hybrid','Remote','Field work']),
 ('Household waste treatment',['Recycling','Composting','Landfill','Other']),('Household internet devices',['Phone','Laptop','Tablet','Desktop']),
 ('Volunteering activities',['Environment','Education','Sport','Other']),('Sports chosen by members',['Badminton','Swimming','Running','Football']),
 ('Uses of city land',['Housing','Parks','Industry','Services']),('School club participation',['Drama','Music','Painting','Design']),
 ('Food container materials',['Plastic','Paper','Reusable','Other']),('Course delivery methods',['Classroom','Online','Hybrid','Independent']),
 ('Types of repair requests',['Clothing','Bicycles','Furniture','Devices']),('Uses of heritage buildings',['Museums','Offices','Community','Vacant']),
 ('Advertising media',['Television','Social media','Print','Outdoor']),('Short journey transport',['Car','Cycle','Bus','Walking']),
 ('Reasons for changing jobs',['Pay','Interest','Location','Other']),('Teenage screen activities',['Study','Games','Creative work','Social media']),
]
STORIES=[
 ('a useful piece of advice','advice','my older cousin','a quiet cafe','list three priorities before opening any apps','stopped switching between unfinished tasks'),
 ('a place where you like studying','study places','my classmate','the public library','reserve a small desk near a window','finished a difficult essay without rushing'),
 ('a skill you learned from a friend','learning skills','my badminton partner','a neighbourhood court','practice a relaxed grip before trying stronger shots','became more consistent and less tense'),
 ('a memorable conversation','conversations','my teacher','a classroom after a lesson','explain why my overview missed the main trend','understood the difference between detail and an overall pattern'),
 ('an object you repaired','repairing things','my sister','our kitchen table','replace a loose button on an old jacket','kept using a favourite item instead of discarding it'),
 ('a time you made a careful purchase','shopping','my friend','a small second-hand shop','compare condition and measurements before deciding','bought a practical coat within my budget'),
 ('a meal you enjoyed preparing','cooking','my younger brother','our apartment kitchen','prepare simple rice, vegetables and a bean dish','shared a relaxed meal and learned to organize the ingredients'),
 ('a routine that helps you','daily routines','my colleague','our office break room','prepare lunch and a short task list the night before','started the day with fewer decisions and less stress'),
 ('a small environmental action','the environment','a neighbour','our building courtyard','set up a labelled container for clean reusable pots','made it easier for neighbours to reuse what they already had'),
 ('a plant you enjoyed caring for','plants','my aunt','our sunny balcony','check the soil before adding water to a small herb plant','kept the plant healthy by observing it rather than following a rigid rule'),
 ('a book you would recommend','books','my school friend','the community reading room','read a short collection of stories and discuss one ending','noticed how a simple scene could suggest a bigger idea'),
 ('a community event you attended','community events','a local volunteer','a neighbourhood library','help arrange a book exchange and welcome first-time visitors','met people with different reading interests'),
 ('a photograph that is important to you','photographs','my best friend','a park near our old school','take a picture after a long walk on graduation day','kept a reminder of a friendship that continued after school'),
 ('a person who helped you feel confident','confidence','a patient photographer','a small portrait studio','practice a comfortable pose and talk before the camera was raised','felt natural rather than forcing an expression'),
 ('a creative activity you tried','creative activities','my art tutor','a weekend classroom','draw a cup using basic shapes and then refine the edges','learned that observation mattered more than a perfect first attempt'),
 ('a challenge you completed','challenges','my roommate','our living room','finish a small drawing every day for one week','became willing to revise instead of abandoning an imperfect idea'),
 ('a useful digital tool','technology','my coworker','a shared office','use a spreadsheet filter to find incomplete records','saved time and checked a claim against the actual entries'),
 ('a mistake that taught you something','mistakes','my supervisor','our team workspace','find and correct a duplicated row before a report was sent','learned to check totals rather than trust a neat-looking table'),
 ('a journey you remember','travel','my cousin','a nearby coastal town','plan a short trip by bus and walk between small attractions','enjoyed travelling slowly and noticed ordinary local details'),
 ('a decision you were pleased with','decisions','my former classmate','a cafe after work','choose a manageable evening course instead of several courses at once','kept studying consistently while meeting other responsibilities'),
]


def base(category,skill,title,objective,materials,instructions,deliverables,answer):
    return {'category':category,'skill':skill,'title':title,'objective':objective,'duration_minutes':60,
      'materials':materials,'instructions':instructions,'deliverables':deliverables,'rubric':rubric_for(category,skill),
      'answer_key':answer,'source':SOURCE,'reference_sources':[{'title':'IELTS official practice formats','url':IELTS_SOURCE}] if category=='IELTS' else []}


def writing(index):
    topic,question,argument,caution,example=ESSAYS[index]
    chart_title,labels=CHART_TOPICS[index]
    a=[46+index%9,24-index%5,18+index%4,0];a[-1]=100-sum(a[:-1])
    b=[a[0]-9-index%4,a[1]+5+index%3,a[2]+8-index%3,0];b[-1]=100-sum(b[:-1])
    years=[2006+index,2026+index]
    chart={'type':'bar' if index%2==0 else 'line','title':chart_title,'unit':'%','categories':labels,
      'series':[{'name':str(years[0]),'values':a},{'name':str(years[1]),'values':b}],
      'source_note':'Original simulated practice figures; not published statistics.'}
    # Line charts place years on the x axis, one series per category.
    if chart['type']=='line':
        chart['categories']=[str(years[0]),str(years[1])]
        chart['series']=[{'name':label,'values':[x,y]} for label,x,y in zip(labels,a,b)]
    task1=f'The figure presents the percentage distribution of {chart_title.lower()} in a fictional town in {years[0]} and {years[1]}. Write a report of at least 150 words, identifying the overall pattern and comparing important figures. Allow 20 minutes.'
    task2=question+' Develop your position with reasons and relevant examples in at least 250 words. Allow 40 minutes.'
    paragraph1=f'The chart compares the proportions of four categories of {chart_title.lower()} in a fictional town in {years[0]} and {years[1]}. The figures are expressed as percentages, so they describe shares rather than the absolute number of people or items in each group.'
    paragraph2=f'Overall, {labels[0].lower()} accounted for the largest share in both years, although its proportion declined. By contrast, the shares of {labels[1].lower()} and {labels[2].lower()} increased. The distribution therefore became less concentrated in the initially dominant category, without a change in which category ranked first.'
    paragraph3=f'In {years[0]}, {labels[0].lower()} stood at {a[0]}%, compared with {a[1]}% for {labels[1].lower()}. By {years[1]}, these figures were {b[0]}% and {b[1]}%, respectively. This represents a fall of {a[0]-b[0]} percentage points in the former and a rise of {b[1]-a[1]} points in the latter.'
    paragraph4=f'The remaining categories were smaller at the beginning of the period. {labels[2]} rose from {a[2]}% to {b[2]}%, while {labels[3].lower()} changed from {a[3]}% to {b[3]}%. The gap between the largest and smallest categories narrowed from {max(a)-min(a)} to {max(b)-min(b)} percentage points. Since no totals are supplied, the chart does not establish whether the actual number in any category rose or fell.'
    essay=f'''Debates about {topic} often focus on a single attractive outcome while overlooking the practical conditions needed to achieve it. {POSITIONS[index]} The needs of the people affected, the available resources and the way a proposal would operate should all influence the decision.

One important consideration is that {argument}. This is more than an abstract benefit: it can change the options available in everyday life. When a policy removes a specific barrier, people are better able to make useful choices for themselves. However, the benefit should be assessed through a clear mechanism rather than an unsupported promise that everyone will gain equally. Access, cost and the experience of different groups are therefore relevant questions, even when the general purpose of a proposal appears reasonable.

A second consideration is that {caution}. Ignoring this difficulty could turn a sensible aim into an ineffective programme. For instance, {example}. This illustrates why implementation deserves as much attention as the original intention. A policy should begin with manageable steps, allow people to raise problems and be adjusted when the evidence shows that an assumption was wrong. Such evaluation need not make a programme unnecessarily complicated; it simply connects spending and effort with the outcome people actually need.

Supporters of a more absolute position might argue that a clear, universal rule would be easier to communicate and administer. That is a legitimate concern, especially where staff and budgets are limited. Nevertheless, simplicity is not always the same as fairness or effectiveness. A consistent principle can still allow proportionate exceptions and targeted support. Explaining those exceptions openly is preferable to pretending that all circumstances are identical.

In conclusion, {POSITIONS[index]} A clear objective and careful implementation are more convincing than relying on a sweeping claim about what one measure can achieve.'''
    material='Category | '+str(years[0])+' (%) | '+str(years[1])+' (%)\n'+'\n'.join(f'{name} | {x} | {y}' for name,x,y in zip(labels,a,b))
    d=base('IELTS','Writing',f'Writing {index+1:02d} · {chart_title} / {topic}',
      'Viết đủ Task 1 có overview và so sánh; Task 2 trả lời đúng mọi vế câu hỏi, giữ quan điểm nhất quán.',
      'Dữ liệu thực hành tự tạo; mỗi năm tổng 100%. Không suy ra số lượng tuyệt đối hay nguyên nhân từ biểu đồ.\n'+material,
      '0–3 đọc đề và chọn hai xu hướng; 3–17 viết Task 1; 17–20 kiểm số liệu. 20–25 lập luận Task 2; 25–55 viết; 55–60 kiểm đáp ứng câu hỏi và ngữ pháp. Bắt đầu bằng bài tự làm, không chép bài tham khảo.',
      'Text hoặc DOCX: Task 1 ≥150 từ và Task 2 ≥250 từ; ghi thời gian, số từ và ba câu tự sửa. Nộp cả hai task của đề này; Task 2 có trọng số gấp đôi.',
      'TASK 1 — REPORT\n'+'\n\n'.join([paragraph1,paragraph2,paragraph3,paragraph4])+'\n\nTASK 2 — COMPLETE ESSAY\n'+essay+
      '\n\nPHÂN TÍCH: Task 1 nhóm xu hướng tăng/giảm, có overview, dùng percentage points cho chênh lệch tuyệt đối; không bịa nguyên nhân. Task 2 nêu quan điểm có điều kiện, giải thích hai luận điểm và ví dụ gắn với vấn đề. Với câu hỏi hai phía, phải thể hiện lợi ích và hạn chế của hai lựa chọn, không chỉ liệt kê. Bài mẫu không có band được chứng nhận.')
    d.update(chart=chart,writing_tasks=[task1,task2],writing_model_answers=[paragraph1+'\n\n'+paragraph2+'\n\n'+paragraph3+'\n\n'+paragraph4,essay])
    from .writing_formats import diversify_starter
    return diversify_starter(d,index)


def speaking(index):
    cue,domain,person,place,action,outcome=STORIES[index]
    questions=[f'Do you enjoy talking about {domain}?',f'When did you first become interested in {domain}?',
      f'Do people in your family share your interest in {domain}?',f'How often do you make time for {domain}?',
      f'Would you like to learn more about {domain}?',f'Has your attitude to {domain} changed since childhood?',
      f'Do you prefer exploring {domain} alone or with someone else?',f'Is there anything about {domain} that you find difficult?']
    p1=[
      f'Yes, especially when the conversation includes a specific experience rather than a list of general opinions. I recently had a useful experience involving {domain}, and explaining it to a friend helped me notice what I had actually learned. I do not talk about it constantly, but I find the subject engaging.',
      f'I became more interested last year, after spending time with {person} at {place}. Before then, I had not given the subject much attention. Seeing a practical example made it feel relevant to my own life, so I started asking questions and trying small things for myself.',
      f'To some extent, although we approach it differently. I tend to focus on what I can learn from an experience, while other relatives enjoy sharing stories about it. When we discuss {domain}, those differences usually make the conversation more interesting rather than causing an argument.',
      f'I do not have a strict schedule, but I try to leave some space for it during the week. A short, focused session is often more useful than waiting for a completely free afternoon. When I am busy, I keep a brief note so I can return to the idea later.',
      f'Definitely. My experience with {person} showed me that there is usually more to understand than the first impression suggests. I would like to learn from someone with more experience, then test the advice in a realistic situation instead of simply collecting information that I never use.',
      f'Yes. When I was younger, I mainly cared about the immediate result and did not think much about the process. Now, with {domain}, I am more willing to compare different approaches and reflect on a mistake. That makes the activity feel less intimidating and more worthwhile.',
      f'I like a combination. Working alone gives me time to notice details and form my own opinion, but another person can point out something I have missed. For example, {person} helped me understand a difficulty without taking over the whole experience or telling me what to think.',
      f'The hardest part is deciding which advice is relevant to my particular situation. It is easy to find confident recommendations, but the circumstances behind them may be different. I usually begin with a small step, observe the result and ask a more specific question before making a bigger change.',
    ]
    p2=f'''I would like to describe {cue} because it changed how I approached an ordinary part of my life. It happened last year, when I was spending time with {person} at {place}. I had gone there with a fairly simple expectation, but the experience turned out to be more useful and memorable than I had anticipated.

At first, I was slightly unsure what to do. I understood the general aim, yet I was concentrating too much on getting an impressive result immediately. {person.capitalize()} noticed this and encouraged me to slow down and pay attention to one manageable step. The suggestion was to {action}. It sounded straightforward, but following it required me to change a habit rather than merely agree with a piece of advice.

We spent a little time trying the approach, discussing what worked and adjusting the parts that did not. I remember one moment when I began to rush again. Instead of criticising me, the other person asked a practical question that made me look at what was happening. That calm response helped me relax and take responsibility for the next attempt.

By the end, I {outcome}. The immediate result mattered, but the more valuable part was understanding how a small, deliberate action could make a difference. I left with something concrete to try again rather than a vague feeling that I should improve.

I still remember this experience because it showed me that progress does not have to be dramatic to be meaningful. It also reminded me how helpful patient support can be when someone is learning. If I encountered a similar situation now, I would begin more calmly and focus on the process as well as the outcome.'''
    p3q=[f'Why can {domain} be important in everyday life?',f'Do younger and older people approach {domain} differently?',
      f'How has technology affected the way people think about {domain}?',f'What role should communities play in helping people understand {domain}?',
      f'Can schools help young people make better decisions about {domain}?',f'How might attitudes to {domain} change in the future?']
    p3=[
      f'I think {domain} can matter because it connects individual choices with everyday consequences. People do not always need specialist knowledge, but they benefit from recognising the options available and considering why a particular choice suits them. A practical example makes this clearer than a slogan. In my own experience, the value came from changing one action and seeing the result, rather than simply being told that the topic was important.',
      f'There can be differences, although age alone is not a reliable explanation. Younger people may be more willing to experiment, whereas older people sometimes draw on a wider range of previous experiences. However, access, responsibilities and personal interests also shape attitudes to {domain}. A young person with limited resources may be cautious, while an older person with support and free time may be very adventurous. I would therefore avoid treating either group as uniform.',
      f'Technology has made information and examples about {domain} easier to find and share. That can help a beginner get started, but it also creates the problem of deciding which advice is relevant and trustworthy. A polished presentation is not necessarily evidence of expertise. People need to ask where a claim comes from, what conditions it assumes and whether it works in their circumstances, rather than judge it only by popularity.',
      f'Communities can provide affordable opportunities to try things, ask questions and meet people with different experiences. In relation to {domain}, a small discussion group or practical session may be more useful than an expensive promotional event. The important point is that people feel comfortable admitting uncertainty. Organisers should offer clear information and accessible participation, while recognising that not everyone wants the same level of involvement or has the same amount of free time.',
      f'Yes, provided that the teaching goes beyond memorising rules. A lesson on {domain} could ask students to compare two realistic options, explain their reasons and reflect on a possible drawback. This would develop judgement rather than require everyone to reach an identical personal decision. Teachers should also make the limits of an example clear, so students can transfer the reasoning to a new situation instead of blindly repeating an answer.',
      f'I expect attitudes to {domain} to become more varied as people encounter different ways of living and more information online. Some may prefer convenient, technology-based solutions, while others may value direct experience and personal contact more strongly. It is difficult to predict one universal trend. What seems likely is that people will need better ways to evaluate claims and adapt general advice to their own priorities, especially when time and resources are limited.',
    ]
    answers='PART 1\n'+'\n\n'.join(f'{i}. {q}\n{a}' for i,(q,a) in enumerate(zip(questions,p1),1))
    answers+='\n\nPART 2 — COMPLETE LONG TURN\n'+p2
    answers+=f'\n\nFOLLOW-UP 1 — Would you recommend a similar experience?\nYes, because it offered a practical lesson that I could use again. I would suggest starting with a manageable step and choosing someone patient to help. The exact result may differ, but reflecting on the experience can still be useful.\n\nFOLLOW-UP 2 — Have you discussed it with anyone since then?\nYes, I told a friend about {person} and what happened at {place}. I focused on the part that changed my approach rather than presenting myself as an expert. My friend then shared a related experience, which made the conversation more useful.'
    answers+='\n\nPART 3\n'+'\n\n'.join(f'{i}. {q}\n{a}' for i,(q,a) in enumerate(zip(p3q,p3),1))
    d=base('IELTS','Speaking',f'Speaking {index+1:02d} · {cue}',
      'Thực hiện một lượt Speaking đủ ba phần, nói tự nhiên, giải thích và minh họa thay vì đọc bài học thuộc.',
      f'Chủ đề Part 1: {domain}; cue card Part 2 và toàn bộ câu hỏi Part 3 ở dưới. Dùng trải nghiệm thật của bạn; câu chuyện trong đáp án chỉ là minh họa hư cấu. Bút, giấy ghi từ khóa, thiết bị ghi âm.',
      '0–8 làm quen chủ đề; 8–22 ghi âm lượt thi thử 11–14 phút: Part 1 4–5 phút, Part 2 một phút chuẩn bị/tối đa hai phút nói và follow-up, Part 3 4–5 phút. 22–40 nghe lại, đánh dấu ngập ngừng và câu khó hiểu; 40–55 ghi lại các câu yếu; 55–60 ghi ba điểm cần sửa.',
      'Một audio lượt đầu không cắt ghép, transcript nếu có; audio lượt sửa và bảng ba câu trước/sau. Nếu chỉ nộp text, app không thể xác minh pronunciation. Ghi rõ đã đọc bài mẫu hay chưa.',answers+
      '\n\nCÁCH HỌC: Part 1 nêu câu trả lời trực tiếp, thêm lý do và một chi tiết. Part 2 dùng quá khứ, một tình huống cụ thể và phản ánh cuối bài. Part 3 mở rộng ra xã hội, phân biệt nhóm và nêu giới hạn. Không học thuộc tên người/địa điểm hư cấu. Lượt mẫu là bài học, không phải band được chứng nhận.')
    d['speaking_tasks']={'part1':{'questions':questions},'part2':{'cue_card':'Describe '+cue+'.',
      'bullets':['what the experience or subject was','when and where it became important to you','who was involved and what happened','why you remember it or value it'],
      'followups':['Would you recommend a similar experience?','Have you discussed it with anyone since then?']},'part3':{'questions':p3q}}
    return d


DRILLS=[
 ('Giao cầu thấp thuận tay','đưa cầu qua lưới và rơi vào ô gần vạch giao cầu ngắn','giao cầu dưới mức lực tối đa, chuẩn bị thả cầu nhất quán','cầu bay quá cao','giảm biên độ đánh và kiểm vị trí tiếp xúc'),
 ('Đổi grip thuận tay và trái tay','đổi cách cầm giữa hai phía mà không siết liên tục','tập chậm với tay thả lỏng, đổi mặt vợt trước khi đưa vợt về vị trí chuẩn bị','cầm quá chặt','giảm tốc độ và chỉ tăng khi đổi grip không nhìn tay'),
 ('Bước lên hai góc trước','trở về vị trí giữa sau mỗi lần tiếp cận góc trước','di chuyển bước nhỏ, chùng nhẹ gối và không vượt tốc độ kiểm soát','đứng lại ở góc sau khi chạm mốc','thêm một nhịp về giữa sau mỗi lượt'),
 ('Đánh cầu sát lưới','đưa cầu rơi sang nửa sân gần lưới','đánh nhẹ với mặt vợt ổn định, không cố cắt xoáy khi chưa kiểm soát','cầu dính lưới','điều chỉnh điểm tiếp xúc và tập tốc độ thấp hơn'),
 ('Nâng cầu từ trước sân','nâng cầu đủ cao về khu vực cuối sân đối diện','phối hợp bước tiếp cận và mặt vợt, bắt đầu với cấp cầu ổn định','chỉ dùng lực cổ tay mạnh','giảm lực, chú ý hướng mặt vợt và tư thế cân bằng'),
 ('Đánh cầu cao sâu','hướng cầu lên cao tới vùng cuối sân đối diện','tập với người cấp cầu nhẹ, xoay thân vừa phải, ưu tiên kiểm soát','đánh khi cầu đã đi quá sau người','đổi vị trí đứng sớm hơn trước khi tăng lực'),
 ('Bỏ nhỏ từ giữa sân','tạo chênh lệch giữa một cú cao sâu nhẹ và một cú đưa cầu ngắn','tập hai hướng cùng chuẩn bị, tốc độ thấp và không ép vai','vung quá mạnh cho cú ngắn','giảm biên độ và ghi điểm rơi thay vì chỉ điểm qua lưới'),
 ('Drive nhẹ hai phía','duy trì đường cầu ngang trong tầm kiểm soát','cặp đôi đứng vừa khoảng cách, thực hiện các lượt ngắn với lực nhẹ','vợt chuẩn bị quá thấp','đưa vợt về vị trí sẵn sàng sau mỗi lần chạm'),
 ('Chọn vùng trống','chọn bên ít được bảo vệ trong tình huống mô phỏng','đọc vị trí đối tác trước khi thực hiện cú đánh kiểm soát','chọn hướng theo thói quen','nói rõ lý do chọn vùng trước khi đánh thử'),
 ('Phối hợp đôi trước và sau','trao đổi vị trí rõ trong bốn tình huống mô phỏng','tập đi bộ vị trí, gọi cầu sớm, không chạy vào đường của bạn cùng sân','cả hai cùng lao vào một quả','thống nhất lời gọi và diễn thử chậm không dùng cầu'),
]


def badminton(i):
    name,target,method,error,fix=DRILLS[i]
    answer=f'''BÀI MẪU — {name}. Mục tiêu quan sát là {target}; tiêu chuẩn này đo một buổi luyện, không kết luận trình độ thi đấu. Bắt đầu với mặt sân khô, khoảng trống đủ rộng và dụng cụ vừa tay. Khởi động nhẹ vai, khuỷu, cổ tay, hông và bước nhỏ; không tập qua cơn đau.
Tổ chức buổi tập: tám phút khởi động, bảy phút xem mục tiêu và diễn thử chậm, hai mươi phút cho bốn hiệp, mỗi hiệp mười lần với nghỉ một phút, mười phút thử một điều chỉnh, mười phút xem bằng chứng và năm phút ghi nhận. Chỉ tăng tốc khi động tác còn kiểm soát; thay đổi một yếu tố mỗi lần để thấy điều chỉnh nào có tác dụng.
Cách thực hiện đúng mục tiêu: {method}. Đặt mốc bằng băng giấy hoặc vật mềm, không đặt vật gây vấp trên đường chạy. Người hỗ trợ cấp cầu đều và đứng ngoài vùng vung vợt. Nếu không có sân, diễn thử chậm và tự ghi rõ không có dữ liệu điểm rơi của cầu; lượt không cầu không được tính thành lượt đánh thành công.
Sai lầm cần nhận diện: {error}. Điều chỉnh phù hợp là {fix}. Không suy từ một ảnh đẹp rằng cả hiệp đã tốt. Quay một đoạn trước điều chỉnh và một đoạn sau ở cùng góc nhìn, giữ tốc độ thật. Ghi số lần đạt mục tiêu trên tổng lần thử; không xóa lượt lỗi khỏi mẫu để làm tăng tỷ lệ.
Bảng log cần có bốn dòng: hiệp 1 đến 4, số lần thử, số đạt, lỗi chủ yếu và mức mệt tự cảm nhận. Tỷ lệ mỗi hiệp bằng số đạt chia số thử nhân 100. Đáp án không điền sẵn kết quả vì bạn chưa thực hiện; số đo thật phải do người học ghi. Tự phản hồi nêu một chi tiết đã kiểm soát tốt, một lỗi có bằng chứng/timecode, một điều chỉnh và cách thử lại. Nếu đau hoặc chóng mặt, dừng buổi luyện và không cố hoàn thành số hiệp.'''
    return base('Cầu lông','',f'Cầu lông {i+1:02d} · {name}',f'Thực hiện {name.lower()} và đo {target}.',
      f'Nhiệm vụ duy nhất: {name}; phương pháp: {method}. Vợt, cầu, sân hoặc khoảng trống an toàn, băng đánh dấu, thiết bị quay. Bảng ghi: hiệp | lần thử | lần đạt | lỗi | mệt (1–5). Lỗi giả định để kiểm tra: {error}.',
      '0–8 khởi động; 8–15 diễn thử; 15–35 bốn hiệp ×10 lần, nghỉ một phút/hiệp; 35–45 thử một sửa đổi; 45–55 xem video/log; 55–60 phản hồi. Không có sân thì tập chậm không cầu và ghi rõ giới hạn. Dừng nếu đau.',
      'Video trước/sau có timecode hoặc chuỗi ảnh rõ + log bốn hiệp; tỷ lệ thật; một lỗi, một sửa đổi và tiêu chí thử lại. Không điền số liệu chưa đo.',answer)


def practical(i,category):
    brand,business,audience,offer,objection,price,format_name=CONTEXTS[i]
    shared=f'Khách hàng giả lập: {brand}, {business}. Đối tượng: {audience}. Sản phẩm: {offer}; giá thực hành {price:,} đồng. Vấn đề: {objection}. Không giả số khách/đơn/chứng thực thật.'
    brief={
      'Content':f'{format_name}; thu hút {audience} mà không hứa kết quả chưa kiểm chứng',
      'Edit':f'dựng phim dọc 30 giây cho {brand}, dùng cấu trúc lỗi → cách thử → minh chứng → lời mời',
      'Bán hàng':f'tư vấn {offer} cho khách nói “{objection}” và “tôi chưa muốn trả {price:,} đồng”',
      'Dạy':f'dạy {audience} kiểm tra một lời hứa về {offer} bằng ví dụ và bằng chứng',
      'Tạo dịch vụ gói gọn':f'đóng gói dịch vụ sản xuất nội dung cho {brand} với ngân sách giả lập {price*10:,} đồng',
    }[category]
    objective=f'Tạo và diễn thử {brief}; có đầu ra hoàn chỉnh, một tiêu chí kiểm chứng và phần tự sửa.'
    if category=='Content':
        skill=SCHEDULE[(i%2)*12+3][1]
        deliver='Kịch bản/bài viết hoàn chỉnh đúng thể loại yêu cầu; 3 hook, caption, CTA, shotlist hoặc các slide; một bản tự sửa và kế hoạch đo. Không chỉ nộp outline.'
        actual_format,facts,script=CONTENT_CASES[i]
        brief=f'{actual_format} cho {brand}: {facts}'
        objective=f'Viết và diễn thử {actual_format.lower()}, truyền đạt đúng dữ kiện và CTA một bước, không bịa kết quả.'
        shared+='\nDữ kiện bắt buộc và khác các bộ khác: '+facts+'\nThể loại: '+actual_format
        answer=f'''ĐẦU RA MẪU — {actual_format} cho {brand}.\n{script}
Caption đầy đủ: “{brand} chia sẻ một cách nhìn thực tế về {offer}. Tình huống và dữ liệu trong bài phục vụ luyện tập, không phải chứng thực khách thật. Trước khi chọn, hãy xem phạm vi và điều kiện phù hợp với mình. Lưu bài để kiểm lại các bước; nếu cần mô tả gói, nhắn CHI TIẾT.”
Ba hook để thử: “Một chi tiết dễ bỏ qua với {offer}”; “Bạn sẽ kiểm gì khi gặp {objection}?”; “Đừng kết luận chỉ từ một hình đẹp”. Chọn một hook khớp đúng nội dung đã viết; hook còn lại là biến thể để đo, không chèn cả ba vào cùng bài. Với carousel, mỗi slide một ý và CTA ở slide cuối. Với bài viết, giữ đoạn mở/tình huống/điểm đổi/kết rõ. Với video, chữ và lời thoại bổ trợ nhau, không đọc mọi dòng chữ dài trên màn hình.
Danh mục hình: bối cảnh rộng, chi tiết chứng minh dữ kiện, thao tác liên quan và khung kết sạch. Không dùng b-roll không liên quan để che việc chưa có ví dụ. Phần trước/sau giữ cùng điều kiện nhìn; review nêu cả phù hợp và hạn chế; phỏng vấn đóng vai phải gắn nhãn mô phỏng.
Checklist: thông tin đúng dữ kiện, đầu ra đúng thể loại, không bịa kết quả, một CTA, chữ dễ đọc và nguồn hình được phép dùng. Tự sửa ghi câu trước/câu sau và lý do. Kế hoạch đo nếu đăng thật: so hai hook trong điều kiện tương đương, ghi số lần hiển thị, lưu, xem đến giữa và hỏi chi tiết. Nếu chưa đăng, ghi chưa có số đo, không lấy số mục tiêu làm kết quả.'''
    elif category=='Edit':
        skill=''
        answer=f'''TIMELINE MẪU 30 GIÂY — {brand}.
00–03: cận vật hoặc chi tiết gợi vấn đề {objection}; lời thoại “Bạn đang chọn {offer}, nhưng còn băn khoăn điều này?” Chữ một dòng, tương phản tốt, nằm trong vùng an toàn. Không dùng tiếng nổ lớn làm người xem giật mình.
03–08: cảnh rộng cho biết bối cảnh {business}; cắt trên hành động chuyển tay hoặc ánh nhìn để người xem hiểu thay đổi cảnh. Lời dẫn “Trước tiên, nói rõ việc bạn cần giải quyết.” Cho thấy một hành động liên quan trực tiếp tới dịch vụ thay vì b-roll ngẫu nhiên.
08–15: hai cảnh minh họa phạm vi {offer}; mỗi cảnh 3–4 giây. Chữ “Nhu cầu” rồi “Phạm vi”. Giữ cùng cân bằng trắng và tránh đẩy saturation khiến màu sản phẩm sai. Lời thoại và hành động phải bổ trợ nhau, không tranh giành chú ý.
15–22: cảnh đối chiếu một giới hạn với cách hỏi thêm. Lời “Nếu lo {objection}, hỏi cách xử lý cụ thể.” Giữ một khoảnh khắc khoảng một giây để người xem đọc; không thêm transition nếu cắt thẳng đã rõ.
22–27: cận bảng giá giả lập {price:,} đồng và thông tin gói. Chữ “Ví dụ luyện tập, xác nhận điều kiện trước khi mua”. Không gắn một review hư cấu như phản hồi khách thật. Âm nhạc chỉ dùng bản tự tạo hoặc có quyền sử dụng, có thể không dùng nhạc.
27–30: lời kết “Nhắn CHI TIẾT để xem phạm vi của {offer}.” Để CTA đủ lâu, kết bằng một khung sạch thay vì thêm đoạn logo kéo dài.
Quy trình âm thanh: nghe lời trên tai nghe và loa laptop; giảm nhạc nếu che giọng, tránh clipping; không suy từ waveform đẹp rằng giọng đã rõ. Quy trình chữ: đọc từng subtitle, kiểm tên {brand}, giá và lỗi chính tả. Export mẫu: MP4, 1080×1920, H.264, tốc độ khung hình theo footage, AAC; xem lại file xuất từ đầu tới cuối. Bàn giao gồm file xuất, timeline có timecode và log ba sửa đổi. Nếu chỉ nộp ảnh timeline, âm thanh và mượt chuyển động còn thiếu bằng chứng; ghi đúng giới hạn này.'''
        deliver='Video dọc 30 giây, timeline 6 đoạn có timecode, ghi thông số xuất và 3 sửa đổi. Nộp footage tự quay hoặc ghi rõ nguồn có quyền dùng; không cần phần mềm trả tiền.'
    elif category=='Bán hàng':
        skill=''
        answer=f'''HỘI THOẠI MẪU — khách {audience}, gói {offer}.
Người bán: “Chào bạn, tôi có thể hỏi bạn đang muốn giải quyết việc gì trước khi giới thiệu gói không?”
Khách: “Tôi quan tâm nhưng {objection}.”
Người bán: “Điều đó khiến bạn khó quyết định ở điểm nào? Bạn đã thử cách gì, và điều gì bạn không muốn lặp lại?” Mục đích là tìm nhu cầu, không dẫn dắt khách phải mua. Ghi lại câu trả lời bằng ngôn ngữ của khách, tách điều biết chắc khỏi giả định.
Khách: “Tôi muốn thử nhưng chưa biết có hợp không.”
Người bán: “Vậy ưu tiên của bạn là hiểu rõ phạm vi và cách thử. {offer} ở {brand} có giá thực hành {price:,} đồng. Trước khi đặt, tôi sẽ gửi phần có trong gói, phần không có, thời gian và điều kiện. Nếu nhu cầu của bạn vượt phạm vi, tôi nói rõ để bạn so lựa chọn khác.”
Khách: “Giá này hơi cao.”
Người bán: “Bạn đang so với ngân sách dự kiến hay với một gói khác? Nếu tiện, mình so đúng cùng phạm vi để xem chênh lệch nằm ở đâu. Tôi không giảm giá bằng cách giấu bớt đầu ra.” Không kết luận khách không có tiền; hỏi và chờ trả lời.
Khách: “Tôi phải nghĩ thêm.”
Người bán: “Được. Tôi gửi thông tin ngắn để bạn cân nhắc. Bạn muốn tôi trả lời thêm điểm nào? Nếu bạn đồng ý, tôi có thể hỏi lại vào thời điểm bạn chọn; còn nếu không, mình dừng ở đây.”
Khách: “Có chắc hiệu quả không?”
Người bán: “Tôi có thể cam kết phạm vi bàn giao, nhưng không hứa một kết quả phụ thuộc cách sử dụng và nhiều yếu tố khác. Với {objection}, ta cần xem điều kiện cụ thể trước.”
Tin nhắn tiếp nối đầy đủ: “Chào bạn, đây là tóm tắt {offer}: nhu cầu đã trao đổi, giá thực hành {price:,} đồng, phạm vi cần xác nhận và bước tiếp theo là xem bản mô tả. Bạn có thể hỏi thêm hoặc từ chối. Tôi chỉ liên hệ lại nếu bạn muốn.”
Checklist chấm: ít nhất ba câu chẩn đoán, nhắc đúng nhu cầu, không bịa bằng chứng, xử lý ba phản đối, một bước tiếp theo có sự đồng ý. Đo khi có diễn thử: đếm lần nói chen, câu hỏi mở và chỗ khách chưa hiểu. Không ghi một giao dịch thật nếu đây chỉ là đóng vai.'''
        deliver='Hội thoại đầy đủ người bán/khách; 3 câu chẩn đoán, 3 phản đối và xử lý, bảng phạm vi/giới hạn, tin nhắn follow-up; audio hoặc video diễn thử nếu có.'
    elif category=='Dạy':
        skill=''
        topic,rule,example_text,questions,answers,transfer,transfer_answer=TEACHING[i]
        brief=f'dạy {audience} hiểu {topic} rồi giải được một tình huống chuyển giao'
        objective=f'Thiết kế bài dạy {topic} 10 phút; kiểm tra hiểu bằng ba câu hỏi và một bài chuyển giao.'
        shared=f'Chủ đề: {topic}. Đối tượng: {audience}. Kiến thức nền và dữ liệu đầy đủ: {rule}\nVí dụ để phân tích: {example_text}\nCâu hỏi kiểm tra: '+' | '.join(questions)+f'\nBài chuyển giao: {transfer}. Không yêu cầu học viên tự tìm nguyên liệu ngoài đề.'
        answer=f'''GIÁO ÁN MẪU HOÀN CHỈNH — {topic}.
Phút 0–1, người dạy nói: “Hôm nay ta học {topic}. Đến cuối bài, bạn sẽ tự giải một trường hợp mới và giải thích vì sao. Trước tiên, bạn đoán lời giải của ví dụ này thế nào?” Đọc {example_text} và chờ người học nêu cách nghĩ. Không cho đáp án ngay; câu trả lời đầu giúp xác định phần cần giải thích.
Phút 1–3, giải thích: “Quy tắc cốt lõi là: {rule}.” Viết từng thành phần trên giấy và dùng lời quen thuộc trước thuật ngữ. Hỏi người học phần nào trong ví dụ ứng với từng thành phần; nếu họ chỉ nhắc lại tên thuật ngữ, quay lại chi tiết cụ thể thay vì kết luận đã hiểu.
Phút 3–5, ví dụ đã giải: {example_text}. Đọc chậm, chỉ rõ bước tính/lý do cho kết luận và giới hạn của ví dụ. Người dạy nói: “Tôi đang chứng minh cách làm với dữ liệu này, không nói mọi tình huống đều giống nhau.” Sau đó đề nghị học viên dùng lời của họ giải thích lại một bước, không đọc lại nguyên văn.
Phút 5–7, hỏi ba câu và trả lời sau mỗi lần người học thử: {questions[0]} Đáp án: {answers[0]}. {questions[1]} Đáp án: {answers[1]}. {questions[2]} Đáp án: {answers[2]}. Khi câu trả lời sai, hỏi họ đã dùng thông tin nào; sửa đúng chỗ suy luận, không gắn nhãn người học yếu.
Phút 7–9, kiểm tra chuyển giao: “{transfer}” Không cho nhìn worked example. Đáp án và lý do: {transfer_answer}. Một câu trả lời đúng mà không giải thích chưa chứng minh hiểu; hỏi thêm “Bạn biết điều đó nhờ dữ liệu hay nhờ giả định?” Ghi lại câu trả lời thật.
Phút 9–10, tổng kết: nhắc lại quy tắc bằng một câu, nêu một lỗi cần tránh và mời học viên tạo ví dụ của họ. Nếu họ im lặng, cho hai lựa chọn rồi yêu cầu giải thích sự khác nhau; khi đã trả lời, quay lại câu hỏi mở. Nếu câu chuyển giao chưa đạt, giữ mục tiêu và thay cách minh họa thay vì tăng tốc.
Bản tự phản hồi mẫu gồm mục tiêu, câu trả lời ban đầu, phần đã giải thích rõ, câu chuyển giao thật và một sửa đổi có timecode. Những ô kết quả để người học điền sau khi diễn thử; không tự bịa số người hiểu. Video giúp xem cách dẫn và tương tác; ảnh bảng chỉ xác minh nội dung hiển thị, chưa xác minh chất lượng giọng nói.'''
        deliver='Giáo án 10 phút đủ lời thoại, 3 câu kiểm tra và đáp án, 1 tình huống chuyển giao mới, phương án học viên im lặng; ghi âm/video diễn thử và tự phản hồi nếu có.'
    else:
        skill='';budget=price*10
        answer=f'''GÓI DỊCH VỤ MẪU — nội dung thử nghiệm cho {brand}.
Khách hàng mục tiêu: chủ {business} muốn giải thích {offer} cho {audience}; vấn đề nội dung cần xử lý là {objection}. Lời hứa bàn giao là một bộ nội dung rõ phạm vi, không phải cam kết tăng doanh thu hay số người xem.
Phạm vi gồm: một cuộc trao đổi brief 20 phút, một kịch bản video dọc 30 giây, một buổi quay tối đa 45 phút bằng điện thoại tại một địa điểm, một file MP4 1080×1920, một caption và một ảnh bìa. Có một vòng sửa dựa trên brief đã duyệt. Không gồm diễn viên, thuê địa điểm, quảng cáo trả tiền, quản trị kênh hoặc quay lại do khách đổi sản phẩm sau khi duyệt.
Quy trình: nhận thông tin và xác nhận quyền dùng hình; thống nhất mục tiêu và người duyệt; gửi kịch bản trước khi quay; quay theo shotlist; dựng bản nháp; nhận một danh sách sửa tập trung; kiểm tra file cuối và bàn giao. Mỗi bước có người chịu trách nhiệm và điều kiện hoàn thành, tránh việc chờ phản hồi bị nhầm thành thời gian sản xuất.
Giá thực hành: {budget:,} đồng cho phạm vi trên. Bảng chi phí mô phỏng chia 40% cho chuẩn bị/quay, 35% cho dựng, 10% cho quản lý/kiểm file và 15% dự phòng. Đây là dữ liệu tập đóng gói, không phải báo giá thị trường. Nếu khách cần thêm cảnh hoặc thêm vòng sửa, đưa một phạm vi mới để duyệt thay vì tự phát sinh phí.
Tiêu chí nghiệm thu: đúng thông tin {offer}, đúng tên {brand}, file mở được trên điện thoại, lời nghe rõ, subtitle không sai chính tả, CTA đúng brief và tài sản có nguồn được phép dùng. Không dùng lượt xem làm tiêu chí nghiệm thu cho phần việc chỉ sản xuất nội dung.
Tin nhắn bàn giao mẫu: “Tôi gửi video, caption, ảnh bìa và ghi chú phạm vi. Bạn kiểm giúp thông tin sản phẩm và file trên thiết bị dự kiến. Nếu cần sửa trong vòng đã thống nhất, gửi một danh sách tập trung kèm timecode. Xin xác nhận phần đã duyệt hoặc điều cần sửa.”
Kiểm nghiệm gói: diễn thử với một người đóng vai chủ cửa hàng, ghi ba câu họ không hiểu và sửa bản mô tả. Nếu chưa có khách thật, ghi chưa kiểm nghiệm thị trường. Một gói dễ hiểu phải giúp khách biết rõ sẽ nhận gì, cần cung cấp gì, phần nào nằm ngoài phạm vi và cách xử lý thay đổi.'''
        deliver='Trang mô tả gói hoàn chỉnh; bảng bao gồm/không bao gồm; quy trình, chi phí giả lập, giá và tiêu chí nghiệm thu; tin nhắn bàn giao, 3 câu hỏi diễn thử và bản sửa.'
    return base(category,skill,f'{category} {i+1:02d} · {brand} · {brief}',objective,shared,
      '0–10 đọc brief và ghi ràng buộc; 10–25 soạn đầu ra; 25–45 diễn thử/hoàn thiện; 45–55 kiểm rubric; 55–60 ghi ba sửa đổi. Dùng dữ liệu trong đề, không cần mua công cụ hoặc đăng công khai.',deliver,answer)


def sources(i):
    brand,business,audience,offer,objection,price,_=CONTEXTS[i]
    groups=['Không gian','Vật chính','Tay thao tác','Chi tiết bề mặt','Trước thao tác','Sau thao tác','Người và vật','Bảng thông tin','Chuyển cảnh','Kết thúc']
    shots=['toàn tĩnh','trung tĩnh','cận tĩnh','góc thấp tĩnh','góc cao tĩnh','đi ngang chậm','tiến gần chậm','lùi nhẹ','đổi nét thủ công nếu máy hỗ trợ','giữ khoảng trống cho chữ']
    lines=[]
    for g,group in enumerate(groups):
        for j,shot in enumerate(shots):
            n=g*10+j+1
            lines.append(f'{n:03d} | {group} của {business} {brand} | {shot} | 3–5 giây | {brand}-{n:03d}.mp4 | ghi lỗi ánh sáng/rung nếu có')
    table='ID | Chủ thể/bối cảnh | Cách quay | Độ dài | Tên file | Kiểm tra\n'+'\n'.join(lines)
    answer=f'''BỘ NGUỒN MẪU — {brand}, phục vụ dựng nội dung về {offer} cho {audience}.
Shotlist ở đề là danh mục đủ một trăm cảnh cần thực hiện, không phải bằng chứng rằng đã quay. Giữ mã 001–100 liên tục; mỗi mã là một clip gốc khác nhau. Nếu chỉ đổi tên một clip, không tính là nguồn mới. Mỗi nhóm có góc toàn, trung, cận và các chuyển động khác nhau để khi dựng không phải lặp một cảnh cho mọi mục đích.
Quy trình thực hiện: khóa hướng quay dọc, làm sạch ống kính, chọn vùng sáng ổn định và kiểm một clip trước khi quay hàng loạt. Nhóm 001–010 giới thiệu không gian; 011–020 xác định vật chính; 021–030 theo dõi thao tác; 031–040 cho chi tiết; 041–050 và 051–060 tạo cặp trước/sau; 061–070 cho quan hệ người/vật; 071–080 cung cấp thông tin; 081–090 nối cảnh; 091–100 dành cho kết/CTA. Không quay thông tin cá nhân hoặc người chưa đồng ý.
Một clip đạt khi chủ thể rõ, chuyển động có mục đích, đầu/cuối đủ dư để cắt và không làm sai màu/thông tin sản phẩm. Với cảnh chi tiết, thay đổi góc và khoảng cách thật; với cảnh tĩnh, giữ máy bằng hai tay hoặc đặt chắc. Nếu chức năng đổi nét không có trên máy, thay bằng một cận tĩnh rõ và ghi điều chỉnh trong log.
Contact sheet phải có một trăm ô, mỗi ô ghi mã trùng tên file. Log cùng mã gồm tên file, nhóm, thời lượng, mục đích dựng và lỗi phát hiện. Không điền “đạt” cho tất cả trước khi xem. Lấy năm clip ở các nhóm khác nhau để kiểm rung, nét và mức sáng, rồi sửa nhóm có cùng lỗi.
Bàn giao mẫu gồm thư mục clip đặt tên {brand}-001.mp4 đến {brand}-100.mp4, contact sheet, log và một đoạn dựng thử kết hợp cảnh toàn/trung/cận. Vì đề dùng bối cảnh giả lập, bạn có thể diễn tại nhà với vật tương ứng; ghi rõ thay đổi. Ảnh contact sheet chỉ chứng minh các khung hình được đưa vào sheet, chưa chứng minh video liên tục hay quyền sử dụng. Nếu chưa quay đủ, nộp đúng số thực có và ghi thiếu mã nào; không nhân bản clip để làm đẹp số lượng.'''
    return base('Quay 100 source','',f'Quay 100 source {i+1:02d} · {brand} · {business}',
      f'Quay 100 clip gốc 3–5 giây cho bối cảnh {business}, có tính sử dụng khi dựng.',
      f'Bối cảnh giả lập {brand}; ưu tiên chủ thể/vật gợi {offer}. Có thể diễn tại nhà và ghi rõ thay thế. Điện thoại, vật liệu sẵn có; không cần mua.\n'+table,
      '0–5 chuẩn bị; 5–40 quay lần lượt 10 nhóm, 10 clip/nhóm; 40–50 đặt tên và contact sheet; 50–57 kiểm log/năm clip; 57–60 ghi thiếu và lỗi. Nếu thời gian không đủ, ghi số thực đạt để lên kế hoạch tiếp, không giả đủ 100.',
      'Contact sheet 100 ô có mã và log 100 dòng; video nguồn hoặc mẫu đại diện, số clip thực có, một đoạn dựng thử và danh sách lỗi/thiếu.',answer)


TEACHING=[
 ('percent và percentage points','Chênh lệch tuyệt đối của hai tỷ lệ là số points; thay đổi tương đối bằng (mới−cũ)/cũ×100%.',
  'Từ 40% lên 60%: tăng 20 percentage points, tăng tương đối 50%.',['40→60 tăng bao nhiêu points?','50% tương đối dùng mẫu số nào?','Có biết số người tăng nếu thiếu tổng không?'],['20 points','40, mức ban đầu','Không, tổng của hai thời điểm có thể khác nhau'],'Từ 80% xuống 60%, tính hai loại thay đổi','Giảm 20 points; relative change −25% vì −20/80×100.'),
 ('trung bình có trọng số','Mỗi nhóm được tính theo số quan sát, không lấy trung bình các tỷ lệ khi quy mô khác nhau.',
  'Nhóm A 8/10 đạt, nhóm B 20/40 đạt: tổng 28/50=56%, không phải (80+50)/2=65%.',['Tổng số người là bao nhiêu?','Tổng đạt là bao nhiêu?','Vì sao 65% sai?'],['50','28','Hai nhóm có cỡ 10 và 40, trọng số khác nhau'],'A có 3/5 đạt, B có 7/15 đạt, tỷ lệ chung?','10/20=50%; phải cộng tử và mẫu của hai nhóm.'),
 ('mean và median','Mean là tổng chia số phần tử; median là phần tử giữa sau sắp xếp, với số phần tử chẵn lấy trung bình hai giá trị giữa.',
  'Dãy 2,3,4,5,26: mean=8; median=4. Một giá trị lớn kéo mean lên.',['Tổng dãy là bao nhiêu?','Giá trị giữa là gì?','Mean có nhất thiết là một giá trị trong dãy?'],['40','4','Không, mean là phép tính'],'Dãy 1,2,2,3,12: mean và median?','Mean=20/5=4; median=2. Không dùng mean để nói mọi người đều có giá trị 4.'),
 ('tương quan và nhân quả','Hai biến cùng thay đổi chưa chứng minh biến này gây ra biến kia; cần xét biến khác và cách đo.',
  'Ngày nóng có cả lượt mua kem và lượt đi bơi tăng; dữ liệu không chứng minh ăn kem khiến người ta đi bơi.',['Hai biến là gì?','Biến thứ ba có thể là gì?','Có thể kết luận nguyên nhân từ bảng này không?'],['Lượt mua kem và lượt đi bơi','Thời tiết/nhiệt độ','Chưa đủ bằng chứng'],'Nơi có nhiều thư viện cũng có nhiều sinh viên. Thư viện có chắc tạo ra sinh viên không?','Không; quy mô dân số, trường học và nhiều yếu tố khác có thể liên quan. Cần nghiên cứu thêm.'),
 ('một hook có lời hứa kiểm chứng được','Hook nêu vấn đề cụ thể và lời hứa mà nội dung thực sự trả được; không phóng đại kết quả.',
  'Hook A “Giỏi ngay sau 1 phút”; hook B “Trong 1 phút, chỉ ra lỗi dùng 20% thay cho 20 points”. B có lời hứa quan sát được.',['A thiếu gì?','B hứa kết quả nào?','Nội dung phải làm gì để giữ lời?'],['Điều kiện và cách xác minh năng lực','Chỉ ra một lỗi cụ thể','Giải thích lỗi và đưa ví dụ đúng'],'Sửa hook “Video này giúp bạn bán gấp đôi ngay”.','Một lựa chọn: “Ba câu hỏi để biết khách đang vướng ở đâu”; nội dung phải đưa đủ ba câu và cách dùng.'),
 ('tính liên tục trong dựng hình','Giữ hành động và thông tin không gian nhất quán khi đổi góc; transition không sửa được cảnh ghép sai hành động.',
  'Cảnh A tay phải cầm cốc; cảnh B cốc đổi tay trái và mức nước khác. Cần quay lại hoặc chọn cảnh có hành động khớp.',['Lỗi nào thấy được?','Transition có tự sửa lỗi này không?','Cần kiểm yếu tố gì?'],['Tay cầm và mức nước không liên tục','Không','Tay, vật, hướng, thời điểm hành động'],'A người mở cửa sang phải, B người đứng trong phòng với cửa vẫn đóng. Sửa thế nào?','Chọn/thu lại cảnh B sau khi cửa đã mở; hoặc dùng cảnh chuyển có chủ đích thể hiện khoảng thời gian, không giả hành động liên tục.'),
 ('câu hỏi chẩn đoán trong bán hàng','Hỏi mục tiêu, hiện trạng và ràng buộc trước khi đề xuất; phản đối về giá chưa chứng minh khách không có nhu cầu.',
  'Khách nói “đắt”. Hỏi họ đang so với ngân sách hay gói khác, rồi so cùng phạm vi, không tự gán động cơ.',['Vì sao hỏi trước giới thiệu?','Cần làm gì với chữ “đắt”?','Có nên hứa doanh thu chắc chắn?'],['Để hiểu đúng nhu cầu','Hỏi nền so sánh','Không, nếu chưa có cơ sở và điều kiện kiểm chứng'],'Khách nói “để tôi nghĩ”. Viết phản hồi tôn trọng.','“Bạn muốn cân nhắc thêm điểm nào? Tôi gửi tóm tắt nếu bạn muốn; chỉ hỏi lại vào lúc bạn đồng ý.”'),
 ('phạm vi và nghiệm thu dịch vụ','Cam kết đầu ra trong quyền kiểm soát; ghi phần gồm/không gồm và cách duyệt thay đổi.',
  'Gói có 1 video, 1 caption, 1 vòng sửa; lượt xem không là đầu ra sản xuất được bảo đảm.',['Một vòng sửa nghĩa gì?','Có bảo đảm lượt xem từ số video không?','Khách đổi brief cần bước gì?'],['Một danh sách sửa theo brief đã duyệt','Không','Xác nhận phạm vi mới trước khi làm thêm'],'Khách yêu cầu thêm địa điểm và quay lại sau khi duyệt. Xử lý thế nào?','Ghi thay đổi, tác động thời gian/chi phí và xin duyệt phạm vi bổ sung; không âm thầm làm rồi thu phí.'),
 ('overview trong IELTS Task 1','Overview chọn đặc điểm bao quát như xu hướng, thứ hạng, thay đổi lớn; không suy nguyên nhân không có trong dữ liệu.',
  'A:50→35, B:20→30, C:15→25, D:15→10. A vẫn lớn nhất; B/C tăng, A/D giảm.',['Nhóm lớn nhất cuối kỳ?','Nhóm nào tăng?','Có biết vì sao A giảm không?'],['A=35','B và C','Không, đề không cho nguyên nhân'],'E:30→45, F:50→25, G:20→30. Viết một overview.','“Overall, E became the largest category, overtaking F, while F was the only category to decline.”'),
 ('tham chiếu tương đối và tuyệt đối trong bảng tính','Khi sao chép, A1 đổi theo vị trí; $A$1 giữ cả cột và dòng.',
  'Ô B2 có =A2*$D$1; kéo xuống B3 thành =A3*$D$1. A2 thay dòng, D1 được giữ.',['A2 thành gì ở B3?','$D$1 có đổi không?','Vì sao dùng dấu $?'],['A3','Không','Để giữ ô chứa hệ số chung'],'C2 có =B2*$F$1; kéo xuống C4 là gì?','=B4*$F$1; B đổi theo dòng, F1 giữ nguyên.'),
]


def livestream(i):
    return varied_livestream(i)


def varied_livestream(i):
    topic,rule,demo,questions,answers,transfer,transfer_answer=TEACHING[i]
    times=['0–2','2–5','5–10','10–14','14–18','18–20']
    lines=[f'“Hôm nay bắt lỗi người dẫn về {topic}. Bạn đoán chỗ dễ hiểu sai trong ví dụ này: {demo}?” Chỉ đọc tình huống trước lời giải; hẹn mở đáp án phút thứ ba.',
      f'“Đúng hẹn, lời giải đầy đủ là: {demo}. Quy tắc: {rule}.” Đọc hai cách nghĩ và giải thích khác biệt, hài với sự hấp tấp của người dẫn.',
      f'“Ta kiểm từng bước: {rule} Bây giờ: {questions[0]}” Đáp án {answers[0]}. “Tiếp: {questions[1]}” Đáp án {answers[1]}. Hỏi lý do thay vì chỉ hỏi đúng/sai.',
      f'“Ai thích thử thách giải trường hợp mới: {transfer}” Đáp án {transfer_answer}. Mời một người nêu điều kiện/giới hạn của kết luận.',
      f'“Người mới thử câu ngắn: {questions[2]}” Đáp án {answers[2]}. Mời người giỏi sửa một câu thiếu điều kiện; nhắc lại quy tắc bằng lời đơn giản.',
      f'“Hôm nay ta có một quy tắc dùng được: {rule} Lưu bảng và tự tạo một ví dụ mới để kiểm xem mình đã hiểu.” Kết đúng giờ, không thêm lời hứa kiến thức chưa dạy.']
    expertise=[{'time':t,'focus':['Nêu vấn đề','Mở lời giải','Chứng minh','Chuyển giao','Phản biện','Tổng kết'][n],'script':lines[n],
      'check':'Ghi câu trả lời và lý do thật. Câu trả lời sai là dữ liệu để dạy lại, không để chế giễu.'} for n,t in enumerate(times)]
    retention=[{'time':t,'focus':['Câu đố','Bình chọn','Cùng tìm lỗi','Thử thách người giỏi','Lượt người mới','Lời hứa đã trả'][n],
      'script':['Mời A/B và hẹn trả lời ở phút thứ ba.','Đọc lựa chọn của cả hai phía; hài hước với lỗi của chính mình.',
      'Cho người xem giải thích lỗi, giữ trò bắt lỗi xuyên suốt nội dung.','Mời người giỏi đưa phản ví dụ hoặc điều kiện giới hạn.',
      'Cho người mới hai lựa chọn rồi hỏi tại sao; người giỏi bổ sung.', 'Nhắc lời hứa ban đầu, xác nhận đã giải và CTA lưu bảng.'][n]+' Nếu không có bình luận, dùng hai lựa chọn giả lập và nói rõ đang diễn thử.',
      'check':'Live thật ghi viewers theo phút/watch time nếu có; diễn một mình ghi chưa có dữ liệu giữ chân.'} for n,t in enumerate(times)]
    answer='KỊCH BẢN MẪU ĐỦ 20 PHÚT\n'+'\n\n'.join(f'{t}: {line}' for t,line in zip(times,lines))
    answer+='\n\nBỐN CÂU KIỂM TRA\n'+'\n'.join(f'{q} → {a}' for q,a in zip(questions,answers))+f'\n{transfer} → {transfer_answer}'
    answer+='\n\nBa câu nối: “Ta đã chọn đáp án, giờ kiểm lý do”; “Đổi tình huống để xem quy tắc có còn dùng được”; “Người mới nắm ý chính rồi, người giỏi thêm điều kiện giúp tôi”. Không chèn một tiết mục hài tách khỏi kiến thức. Người dẫn có thể đùa về lỗi của mình, không làm nhục người sai. Nếu im lặng, đọc hai cách nghĩ giả lập, tự so sánh rồi mời câu hỏi; không tạo tài khoản giả hay đóng giả bình luận thật.\nChecklist trước live: dữ liệu và lời giải khớp, mỗi đoạn có câu dẫn/câu hỏi/câu nối, mở lời giải đúng hẹn, không hứa kết quả học tập chưa đo, có lượt phù hợp cả hai trình độ. Checklist sau live: xem timecode ba đoạn gây khó hiểu và sửa lời dẫn. Nếu có số liệu thật, đối chiếu mốc viewers với hành động đang diễn ra; việc viewers giảm không tự chứng minh một câu nói gây ra giảm. Nếu diễn thử một mình, chỉ đánh giá kịch bản và cách dẫn, không ghi đã giữ chân thành công. Ảnh bảng không chứng minh giọng nói; cần ghi âm/video phù hợp để đánh giá thêm.'
    d=base('Livestream',SCHEDULE[(i%2)*12+9][1],f'Livestream {i+1:02d} · Bắt lỗi về {topic}',
      'Diễn thử live 20 phút có một trò giữ chân chủ lực và một kiến thức chủ lực, đủ thử thách cho người giỏi và lối vào cho người mới.',
      f'Chủ đề: {topic}. Kiến thức nền: {rule}\nVí dụ: {demo}\nBa câu kiểm tra: '+' | '.join(questions)+f'\nChuyển giao: {transfer}. Dùng giấy/bút và thiết bị ghi; không phải live công khai. Kiến thức và dữ liệu trong đề đủ để viết kịch bản.',
      '0–10 chuẩn bị; 10–25 soạn hai bảng và lời thoại; 25–45 diễn thử; 45–55 xem lại; 55–60 ghi ba sửa đổi. Không mở đáp án khi chưa thử tự giải; ghi nếu có tham khảo.',
      'Hai bảng sáu đoạn đủ lời thoại, bốn câu hỏi/đáp án, ba câu nối, checklist, video/timecode; viewers nếu có dữ liệu live thật, nếu không ghi chưa đo.',answer)
    d.update(retention_element='Bắt lỗi người dẫn: chọn A/B, chờ lời giải đúng hẹn, tự giải thích và phản biện; hài hước với lỗi của người dẫn.',
      expertise_element=f'{topic}: một quy tắc, ví dụ đã giải và trường hợp chuyển giao có kiểm tra lý do.',livestream_expertise=expertise,livestream_retention=retention)
    return d


def bank_set(i):
    # Match the schedule, including the second Writing/Speaking at slots 11/12.
    lessons=[writing(i*2),speaking(i*2),badminton(i),practical(i,'Content'),practical(i,'Edit'),
      practical(i,'Bán hàng'),practical(i,'Dạy'),sources(i),practical(i,'Tạo dịch vụ gói gọn'),livestream(i),writing(i*2+1),speaking(i*2+1)]
    for lesson in lessons:validate_assignment(lesson,lesson['category'],lesson['skill'])
    return lessons


def install_bank(engine,count=10):
    """Idempotent install: no scores, submissions or artificial user progress."""
    store=engine.store;installed=[]
    for i in range(count):
        lesson=create_set(store,time.time(),'codex-authored',f'original-bank-v2-{i+1}')
        if lesson['published']:installed.append(lesson['cycle']);continue
        for slot,data in enumerate(bank_set(i),1):
            seq=(lesson['cycle']-1)*12+slot
            if store.one('SELECT id FROM assignments WHERE seq=?',(seq,)):continue
            validate_novelty(store,data,data['category'],data['skill'])
            save_exercise(store,lesson['cycle'],slot,data)
        prepare_assets(engine,lesson['cycle'])
        publish_set(engine,lesson['cycle'],notify=False)
        installed.append(lesson['cycle'])
    folder=store.root/'practice-bank';folder.mkdir(exist_ok=True)
    tasks=store.rows("SELECT a.* FROM assignments a JOIN lesson_sets l ON (a.seq-1)/12+1=l.cycle WHERE l.seed_key LIKE 'original-bank-v2-%' ORDER BY seq")
    manifest={'source':SOURCE,'sets':installed,'count':len(tasks),'fingerprints':[fingerprint(json.loads(r['body'])) for r in tasks]}
    (folder/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    store.event('bank',f'Đã thêm {len(installed)} bộ tạo sẵn · {len(tasks)} đề đầy đủ và đáp án. Chưa có bài làm/điểm giả.')
    return installed
