"""An original, complete Speaking practice set; not official exam questions."""
from .curriculum import rubric_for


def speaking_parts(tasks):
    p1,p2,p3=tasks['part1'],tasks['part2'],tasks['part3']
    return [
        'PART 1 · 4–5 minutes\n'+'\n'.join(f'{i}. {q}' for i,q in enumerate(p1['questions'],1)),
        'PART 2 · 1 minute preparation, up to 2 minutes speaking\n'+p2['cue_card']+'\nYou should say:\n'+'\n'.join('• '+b for b in p2['bullets'])+'\nFollow-up questions:\n'+'\n'.join(p2['followups']),
        'PART 3 · 4–5 minutes\n'+'\n'.join(f'{i}. {q}' for i,q in enumerate(p3['questions'],1))]


def speaking_sample():
    tasks={
        'part1':{'questions':[
            'Do you work or are you a student?',
            'What do you enjoy most about your work or studies?',
            'Is there a skill you would like to learn in the future?',
            'Do you prefer learning alone or with other people?',
            'How often do you use videos to learn something new?',
            'What do you usually do when you find a task difficult?',
            'Did you have a favourite hobby when you were a child?',
            'Has the way you spend your free time changed?']},
        'part2':{'cue_card':'Describe a practical skill that you learned from another person.',
            'bullets':['what the skill was','who taught you','how you learned it','and explain why learning this skill was useful to you'],
            'followups':['Do you still use this skill regularly?','Would you like to teach this skill to someone else?']},
        'part3':{'questions':[
            'What makes someone a good teacher of practical skills?',
            'How does learning a practical skill differ from learning a theoretical subject?',
            'Can online videos replace learning from a teacher in person?',
            'Should schools spend more time teaching practical skills?',
            'Why do some adults stop learning new skills?',
            'Who should be responsible for helping workers learn new skills: individuals, employers or governments?']}}
    answers='''ĐÁP ÁN THAM KHẢO ĐẦY ĐỦ — không có một đáp án duy nhất; dùng để học cách phát triển ý, không học thuộc.
PART 1 · trả lời tự nhiên khoảng 20–30 giây/câu
1. I'm a university student, and I also work on small video projects in my spare time. My studies give me a theoretical foundation, while those projects let me try things out and see what actually works.
2. I enjoy the moment when an abstract idea becomes something useful. For example, I recently applied a lesson about audience attention to a short video. Seeing how a small change affected the clarity of the message made the theory much more memorable.
3. I'd like to become better at speaking in public. I can explain an idea to a friend quite comfortably, but addressing a larger group still makes me nervous. It would be useful for presentations and for teaching other people.
4. I prefer a combination. Working alone gives me time to make mistakes without feeling embarrassed, but learning with someone else exposes gaps that I might miss. Usually I practise independently first and then ask for feedback.
5. Probably three or four times a week, especially when I need to see a process rather than just read about it. I pause the video and copy one step at a time. Watching the whole thing without practising doesn't help me very much.
6. I break it into smaller steps and try to identify exactly where I'm getting stuck. If that doesn't work, I ask someone a specific question. Saying “I don't understand anything” is less useful than explaining the particular step that confuses me.
7. Yes, I used to draw little comic strips. They weren't particularly impressive, but I liked inventing characters and showing the pictures to my friends. It was a simple way to tell stories before I knew anything about editing videos.
8. Definitely. As a child, I had long stretches of free time and chose activities quite spontaneously. Now I have to plan around deadlines, so I tend to choose shorter activities, such as a quick badminton session or a small creative project.

PART 2 · bài nói tham khảo khoảng 2 phút; đo bằng bản ghi của chính bạn
I'd like to talk about learning to edit a short video, which a friend taught me last year. At the time, I wanted to make a brief introduction to a local badminton group, but I had no idea how to turn a collection of clips into a story.

My friend had been editing videos for several years. Rather than show me every button in the software, she asked me one question: what should the viewer understand by the end? That was surprisingly difficult to answer. Eventually, I decided the video should show that beginners could join the group without already being good players.

We selected eight clips and arranged them into a beginning, a middle and an ending. She demonstrated how to cut one scene, and then made me do the next one myself. Whenever I added an unnecessary effect, she asked whether it helped communicate the message. In most cases, it didn't. The hardest part was balancing the music with the speech, because I initially focused on how exciting the music sounded rather than whether the words were clear.

After a few attempts, I produced a thirty-second video. It wasn't a professional masterpiece, but it had a clear message and the speech was easy to hear. Since then, I've used the same approach for several small projects: decide on the message, choose relevant material and remove anything that distracts from it.

What made the experience useful wasn't simply learning a piece of software. I learned to make decisions for the audience, and that has helped me explain ideas more clearly in other situations as well.

Part 2 follow-up 1. Yes, I use it whenever I make a short video for a project. Even when the software changes, the principle of putting the message first remains useful.
Part 2 follow-up 2. I would. I'd probably start with a very small project so the learner could finish something, rather than overwhelm them with all the features at once.

PART 3 · ý chính → giải thích → ví dụ/đối chiếu → giới hạn; khoảng 40–60 giây/câu
1. A good teacher makes the process visible and gives learners a chance to try it. Simply demonstrating an expert performance can be discouraging because the small decisions are hidden. For example, a badminton coach can explain why a player returns to the centre after a shot, then let a beginner practise that movement slowly. Feedback also needs to be specific: “shorten your final step” is more actionable than “do it better”. Of course, what works for a complete beginner may be too slow for someone with experience, so a teacher needs to adapt.
2. Practical learning usually involves a cycle of attempting something, observing the result and adjusting. Theory often begins with concepts that can be discussed before being applied. However, I wouldn't treat them as completely separate. Understanding the physics behind a movement can improve practical training, while doing an experiment can reveal why a theoretical assumption matters. The main difference is the evidence of success: a learner may explain a technique correctly and still struggle to perform it consistently.
3. Videos can replace some explanations, particularly for simple tasks where learners can pause and repeat each step. They also make expertise available to people who cannot attend a class. What they usually lack is feedback tailored to the learner. A video cannot easily tell you that your grip or posture differs from the demonstration. For complex or physical skills, I would combine videos with occasional guidance from a teacher. The balance depends on the task and the learner's experience, rather than the technology alone.
4. Yes, provided practical activities support clear learning goals and don't simply crowd out core subjects. Budgeting, communication and basic digital skills can help students connect school with everyday life. Schools could integrate some of them into existing lessons: a maths class might compare the cost of different service packages. There are constraints, though, including equipment and teacher preparation. I would favour a few well-designed activities with feedback over adding many compulsory subjects without enough support.
5. Time is one reason, especially for people balancing work with family responsibilities. Another is the discomfort of becoming a beginner again after feeling competent in a familiar job. If mistakes are treated as embarrassing, adults may avoid situations where their weaknesses are visible. Cost and access also matter, so it would be unfair to describe everyone who stops learning as unmotivated. Short, affordable courses and a supportive learning environment can make continued learning more realistic.
6. Responsibility should be shared, but each group has a different role. Individuals need to identify their goals and make an effort to practise. Employers should support training that their workers need, ideally with time as well as funding. Governments can improve access for people whose employers cannot provide that support, such as through local training programmes. The challenge is preventing training from becoming a box-ticking exercise. A course is only useful if people can apply what they learn and receive feedback on the result.

TỰ KIỂM & SỬA LỖI
Fluency: ghi timecode những chỗ ngập ngừng kéo dài; thử nói lại bằng câu ngắn hơn, không chỉ tăng tốc.
Lexical resource: dùng từ đúng ngữ cảnh như actionable feedback, tailored guidance, learning goals; diễn đạt lại khi quên từ. Không nhồi idiom.
Grammar: kết hợp câu đơn rõ với mệnh đề điều kiện/đối chiếu đúng. Kiểm soát thì khi kể sự kiện đã qua và nói thói quen hiện tại.
Pronunciation: nhờ người nghe bản ghi kiểm tra độ dễ hiểu, trọng âm và ngữ điệu. Transcript không chứng minh phát âm; điểm này để chưa chấm nếu chưa có người nghe xác minh.
Bài tham khảo này không có band được chứng nhận. Thay ví dụ bằng trải nghiệm thật của bạn. Không ghi rằng đã luyện hay đã nói trôi chảy nếu chỉ đọc văn bản.'''
    return {'category':'IELTS','skill':'Speaking','title':'Speaking full test: learning a practical skill',
        'objective':'Hoàn thành Speaking Part 1, Part 2 và Part 3; phát triển ý tự nhiên và ghi lại ba điểm cần sửa để tiến từ khoảng 6.5 hướng tới 8.0.',
        'duration_minutes':60,
        'materials':'Một bộ câu hỏi Speaking tự biên soạn đầy đủ bên dưới; điện thoại hoặc máy tính ghi âm, giấy và bút cho cue card. Không cần tìm đề ngoài. Đây là bài luyện, không phải bài thi IELTS chính thức.',
        'instructions':'0–5 phút: kiểm tra ghi âm và đọc cách làm, chưa mở đáp án; 5–19: diễn thử bài 11–14 phút, Part 1 trong 4–5 phút, Part 2 chuẩn bị 1 phút/nói tối đa 2 phút và 1–2 câu hỏi ngắn, Part 3 trong 4–5 phút; 19–35: nghe lại và ghi timecode; 35–48: luyện lại ba đoạn khó; 48–57: viết tự phản hồi và đối chiếu rubric; 57–60: nộp audio và ghi rõ có/không tham khảo đáp án. Không chuẩn bị câu trả lời Part 1/3 trong lượt diễn thử. Có thể nhờ bạn đọc câu hỏi; khi luyện một mình, dừng bản ghi ngắn để đọc câu kế tiếp và ghi rõ cách mô phỏng.',
        'deliverables':'Nộp audio đủ Part 1, Part 2 và Part 3, đánh dấu timecode bắt đầu từng phần; transcript nếu có; ghi chú cue card một phút; ba lỗi có timecode và bản sửa; tự khai việc xem đáp án. DOCX chứa transcript/ghi chú có thể đi kèm. App phân tích nội dung từ transcript, còn Pronunciation cần người nghe thực tế bổ sung; nếu thiếu bằng chứng, chưa báo band tổng.',
        'rubric':rubric_for('IELTS','Speaking'),'speaking_tasks':tasks,
        'speaking_parts':speaking_parts(tasks),'answer_key':answers}
