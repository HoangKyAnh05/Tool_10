"""A durable rotation across numerical visuals, maps, processes and devices."""
import copy,json
from .charts import FORMAT_TYPES

FORMAT_NAMES={'bar':'biểu đồ cột','line':'biểu đồ đường','pie':'biểu đồ tròn','table':'bảng số liệu','process':'quy trình','map':'bản đồ / mặt bằng','mixed':'hai biểu đồ kết hợp','diagram':'sơ đồ thiết bị'}


def expected_format(store,seq):
    count=store.one("SELECT count(*) AS n FROM assignments WHERE archived=0 AND skill='Writing' AND seq<?",(seq,))['n']
    return FORMAT_TYPES[count%len(FORMAT_TYPES)]


def format_prompt(kind):
    common='TASK 1 BẮT BUỘC dạng '+kind+' ('+FORMAT_NAMES[kind]+'). Không đổi sang dạng khác. chart.type="'+kind+'". '
    schemas={
      'bar':{'type':'bar','title':'','unit':'%','categories':['A','B'],'series':[{'name':'Year','values':[60,40]}]},
      'line':{'type':'line','title':'','unit':'units','categories':['2010','2015','2020'],'series':[{'name':'Group','values':[30,40,50]}]},
      'pie':{'type':'pie','title':'','unit':'%','categories':['A','B'],'series':[{'name':'Year 1','values':[60,40]},{'name':'Year 2','values':[45,55]}]},
      'table':{'type':'table','title':'','unit':'units','categories':['A','B'],'series':[{'name':'Year','values':[60,40]}]},
      'process':{'type':'process','title':'','cyclical':False,'stages':['4–9 complete stages in order']},
      'map':{'type':'map','title':'','layouts':[{'name':'Before / year','features':[{'label':'Building name','x':5,'y':5,'w':35,'h':30}]},{'name':'After / year','features':[{'label':'New building','x':5,'y':5,'w':35,'h':30}]}]},
      'diagram':{'type':'diagram','title':'','layouts':[{'name':'Device / labelled components','features':[{'label':'Component and purpose','x':5,'y':5,'w':35,'h':30}]}]},
      'mixed':{'type':'mixed','title':'','panels':[{'type':'bar','title':'Panel A','unit':'units','categories':['A','B'],'series':[{'name':'Year','values':[60,40]}]},{'type':'line','title':'Panel B','unit':'units','categories':['2010','2020'],'series':[{'name':'Metric','values':[20,40]}]}]},
    }
    extra='Mọi nhãn và dữ liệu trong materials, đề và đáp án phải khớp hình. '
    if kind=='pie':extra+='Mỗi series là một hình tròn, tổng values phải đúng 100%; 2–6 categories. '
    if kind=='process':extra+='4–9 bước, mỗi nhãn 8–180 ký tự, thể hiện đầu vào, chuyển đổi và đầu ra; natural hoặc manufacturing, nêu rõ cyclic nếu có. '
    if kind in ('map','diagram'):extra+='Mỗi layout có 3–8 features không chồng nhau. Tọa độ x,y,w,h là phần trăm vùng hình 0–100, w/h≥8, x+w≤100, y+h≤100. Map: hai thời điểm cùng hướng bắc, thể hiện những gì đổi và giữ nguyên. Diagram: một thiết bị gồm các bộ phận ghi nhãn rõ, mô tả cấu tạo/chức năng; không bịa công nghệ thực tế. '
    if kind=='mixed':extra+='ĐÚNG hai panels khác type trong bar/line/pie/table; có đủ số liệu riêng từng hình và quan hệ cùng chủ đề; đáp án bao quát cả hai hình. '
    return common+extra+'Chart schema cho dạng này THAY THẾ chart schema trước: '+json.dumps(schemas[kind],ensure_ascii=False)+'\nwriting_model_answers BẮT BUỘC là mảng [bài Task 1 hoàn chỉnh ít nhất 150 từ, bài Task 2 hoàn chỉnh ít nhất 250 từ], đồng thời chép hai bài vào answer_key kèm phân tích.'


def validate_format(data,kind):
    if data.get('chart',{}).get('type')!=kind:raise ValueError('Task 1 phải luân phiên đúng dạng '+kind+', không dùng lại dạng khác.')
    answers=data.get('writing_model_answers')
    if not isinstance(answers,list) or len(answers)!=2 or any(not isinstance(a,str) for a in answers) or len(answers[0].split())<150 or len(answers[1].split())<250:
        raise ValueError('Writing cần writing_model_answers gồm hai bài mẫu đủ ít nhất 150/250 từ.')
    return data


def feature(label,x,y,w=35,h=25):return {'label':label,'x':x,'y':y,'w':w,'h':h}


def diversify_starter(data,index):
    d=copy.deepcopy(data);kind=FORMAT_TYPES[index%len(FORMAT_TYPES)];chart=d['chart'];chart['type']=kind
    if kind in ('bar','pie','table') and len(chart['categories'])==2 and len(chart['series'])==4:
        series=chart['series'];years=chart['categories']
        chart['categories']=[s['name'] for s in series];chart['series']=[{'name':year,'values':[s['values'][i] for s in series]} for i,year in enumerate(years)]
    if kind=='line' and len(chart['categories'])==4:
        labels=chart['categories'];series=chart['series'];chart['categories']=[s['name'] for s in series]
        chart['series']=[{'name':label,'values':[s['values'][i] for s in series]} for i,label in enumerate(labels)]
    title=chart['title'];model=d['writing_model_answers'][0];material=d['materials']
    if kind in ('process','map','diagram'):
        chart,model,material=diagram_starter(kind,index)
        title=chart['title']
    elif kind=='mixed':
        chart['type']='bar';chart['title']=title+': category shares'
        second={'type':'line','title':title+': total participants','unit':'people','categories':['2010','2015','2020','2025'],
          'series':[{'name':'Participants','values':[900+index*10,1080+index*10,1210+index*10,1470+index*10]}],
          'source_note':'Original simulated practice data.'}
        chart={'type':'mixed','title':title+' — shares and totals','panels':[chart,second],'source_note':'Original simulated practice data.'}
        numbers=second['series'][0]['values']
        model=model.rsplit('Since no totals are supplied,',1)[0]+f'The line graph additionally shows the total number of participants rising from {numbers[0]} in 2010 to {numbers[1]} in 2015 and {numbers[2]} in 2020, before reaching {numbers[3]} in 2025. The increase over the full period was {numbers[3]-numbers[0]} people. This indicates growth in overall participation alongside the shift in category shares. However, the years of the two visuals differ, so they cannot be multiplied to calculate category totals for a particular year.'
        material+='\nSecond visual: year | total participants\n'+'\n'.join(f'{year} | {n}' for year,n in zip(second['categories'],numbers))
    d['chart']=chart;d['materials']=material
    d['instructions']=d['instructions'].replace('chọn hai xu hướng','chọn các đặc điểm chính').replace('kiểm số liệu','kiểm dữ liệu / chi tiết hình')
    if kind in ('process','map','diagram'):
        noun={'process':'diagram','map':'two maps','diagram':'labelled diagram'}[kind]
        d['writing_tasks'][0]=f'The {noun} below show {title.lower()}. Summarise the information by selecting and reporting the main features, and make comparisons where relevant. Write at least 150 words. Spend 20 minutes on this task.'
    elif kind=='mixed':d['writing_tasks'][0]='The bar chart and line graph below show '+title.lower()+'. Summarise both visuals, selecting the main features and making comparisons where relevant. Write at least 150 words in 20 minutes.'
    else:d['writing_tasks'][0]=d['writing_tasks'][0].replace('The figure','The '+{'bar':'bar chart','line':'line graph','pie':'pie charts','table':'table'}[kind])
    d['title']=f'Writing {index+1:02d} · {title} / '+d['title'].split(' / ',1)[1]
    d['writing_model_answers'][0]=model
    d['answer_key']='TASK 1 — COMPLETE REPORT\n'+model+'\n\nTASK 2 — COMPLETE ESSAY\n'+d['writing_model_answers'][1]+'\n\nPHÂN TÍCH: Nêu overview và các chi tiết quan trọng đúng hình; không suy diễn nguyên nhân, số liệu, vật liệu hoặc vị trí ngoài đề. Task 2 phải giữ quan điểm rõ và trả lời đủ mọi vế. Bài mẫu luyện tập, không có band được chứng nhận.'
    d['task1_format']=kind;d['task1_format_label']=FORMAT_NAMES[kind]
    return validate_format(d,kind)


def diagram_starter(kind,index):
    note='Original schematic created for IELTS practice; not a real-world technical specification.'
    if kind=='process':
        if index<8:
            title='The production of recycled paper notebooks'
            stages=['Waste paper collection','Sorting: remove unsuitable material','Shredding selected paper','Mixing shredded paper with water','Screening the pulp to remove contaminants','Pressing pulp into sheets','Drying the sheets','Cutting and binding notebooks']
            model='''The diagram illustrates how discarded paper is converted into notebooks. Overall, this is a linear manufacturing process with eight stages, beginning with the collection of waste paper and ending with the cutting and binding of the dried sheets. The material is sorted and cleaned before it is shaped into a new product.

At the start, waste paper is collected and then sorted so that unsuitable material can be removed. The selected paper is subsequently shredded into smaller pieces. These pieces are mixed with water to produce pulp, which is then screened. This screening stage removes contaminants before the pulp is used to form the notebooks.

The next stage involves pressing the cleaned pulp into sheets. The sheets are dried before they are cut to the required size. Finally, the cut sheets are bound together to produce notebooks. Collection and preparation therefore occupy the earlier part of the process, while shaping and finishing occur later. No quantities, temperatures or processing times are specified, and the diagram does not show a return path from the completed notebooks to the collection stage. It should consequently be described as a sequence rather than a cycle.'''
        else:
            title='The preparation of dried apple slices'
            stages=['Harvest ripe apples','Wash apples with water','Remove cores and slice apples','Arrange slices on drying trays','Dry slices with warm air','Cool dried slices','Seal portions in labelled bags','Pack bags for distribution']
            model='''The diagram shows the stages involved in preparing dried apple slices for distribution. Overall, the process consists of eight successive stages, starting with harvesting and finishing with packing. The apples are cleaned and cut before they are dried, and cooling takes place before the finished portions are sealed.

First, ripe apples are harvested and washed with water. Their cores are then removed, and the fruit is cut into slices. The prepared slices are arranged on drying trays, which allows the sliced fruit to enter the drying stage. Warm air is used at this point, although the diagram does not specify a temperature or the length of time required.

After drying, the slices are cooled. Portions of the cooled product are subsequently sealed in labelled bags. In the final stage, these bags are packed for distribution. The sequence thus moves from the preparation of the fruit to the removal of moisture, followed by packaging of the finished product. Washing and slicing precede drying, whereas sealing and packing take place afterwards. The diagram presents a linear operation and contains no recycling loop, additional ingredients or information about the weight of the portions.'''
        chart={'type':kind,'title':title,'stages':stages,'cyclical':False,'source_note':note}
        return chart,model,'Dữ liệu sơ đồ thực hành; chỉ mô tả các bước sau, không thêm nhiệt độ/thời gian không có.\n'+'\n'.join(f'{i}. {s}' for i,s in enumerate(stages,1))
    if kind=='map':
        if index<8:
            title='Changes to a neighbourhood park between 2000 and 2025'
            before=[feature('Flower garden',5,5),feature('Pond',60,5),feature('Open grass',5,43),feature('Playground',60,43),feature('South entrance',30,82,40,12)]
            after=[feature('Cafe',5,5),feature('Pond',60,5),feature('Sports court',5,43),feature('Larger playground',55,40,43,34),feature('South entrance',30,82,40,12)]
            model='''The maps compare a neighbourhood park in 2000 and 2025. Overall, the park became more focused on recreation and visitor facilities. The flower garden and open grass area were replaced, while the pond and southern entrance remained in their original positions. The playground also occupied a larger area in the later plan.

In 2000, a flower garden stood in the north-western part of the park, opposite a pond in the north-east. An area of open grass was located to the south of the garden, in the western section. The playground was on the eastern side, below the pond. Visitors entered through the entrance in the centre of the southern boundary.

By 2025, a cafe had taken the place of the flower garden. A sports court had also been constructed on the former open grass area. On the opposite side of the park, the playground had been enlarged and extended slightly towards the centre. In contrast, the north-eastern pond and the southern entrance were retained. The maps therefore indicate a change in the use of the western areas and an expansion of an existing recreational feature, rather than a relocation of all the park facilities.'''
        else:
            title='The redevelopment of a village library between 1998 and 2028'
            before=[feature('Adult shelves',5,5),feature('Children shelves',60,5),feature('Reading tables',5,43),feature('Storage room',60,43),feature('Reception',30,82,40,12)]
            after=[feature('Adult shelves',5,5),feature('Children activity area',55,5,43,30),feature('Computer desks',5,43),feature('Meeting room',60,43),feature('Reception',30,82,40,12)]
            model='''The plans show how a village library is redeveloped between 1998 and 2028. Overall, the building changes from a space dominated by conventional reading and storage areas to one offering digital access and group activities. The adult shelves and reception are retained, while three other areas are given different functions.

In the earlier plan, the adult shelves are in the north-western section, opposite the children's shelves in the north-east. Reading tables occupy the south-western part of the main floor, and a storage room is situated on the eastern side below the children's section. Reception stands centrally along the southern boundary.

The later plan keeps the adult shelves in the same location and leaves reception unchanged. However, the children's shelves are replaced by a larger activity area, which extends further towards the centre of the building. The reading tables are converted into computer desks, while the former storage room becomes a meeting room. These changes introduce facilities for computer use and meetings without moving the two retained features. The plans show relative positions and functions, but do not provide dimensions or the number of users that each new area can accommodate.'''
        chart={'type':kind,'title':title,'layouts':[{'name':'2000' if index<8 else '1998','features':before},{'name':'2025' if index<8 else '2028','features':after}],'source_note':note}
        positions=['north-west','north-east','south-west','south-east','southern centre']
        return chart,model,'Mặt bằng thực hành, hướng Bắc ở trên, không theo tỷ lệ; vị trí và diện tích tương đối thể hiện trên hình.\n'+'\n'.join(l['name']+': '+'; '.join(f"{f['label']} — {pos}" for f,pos in zip(l['features'],positions)) for l in chart['layouts'])
    if index<8:
        title='The components of a simple rainwater collection unit'
        items=[feature('Collection funnel',30,3,40,17),feature('Inlet pipe',40,25,20,13),feature('Mesh filter',20,43,60,12),feature('Storage tank',15,60,70,22),feature('Outlet tap',70,87,25,10)]
        model='''The labelled diagram shows the components of a simple unit for collecting rainwater. Overall, the device consists of an upper collection section, a filter and a storage section, together with an outlet. The components are arranged mainly vertically, with the collection funnel at the top and the outlet tap near the bottom on the right.

The collection funnel is the highest part of the unit and is positioned centrally above an inlet pipe. The pipe sits between the funnel and the mesh filter. The filter is wider than the pipe and extends across the central section of the diagram. Below it, the storage tank occupies a broad area in the lower half of the unit.

The outlet tap is attached at the lower right-hand side, beneath the tank in the schematic arrangement. This layout separates the area where water is collected from the area where it is stored, with the filter between them. Although the relative positions of the components are clear, the diagram is not drawn to scale and provides no capacity, flow rate or dimensions. It also does not indicate that the stored water is suitable for drinking, so no claim about water quality can be made from the drawing alone.'''
    else:
        title='The layout of a solar-powered bicycle charging shelter'
        items=[feature('Solar panels',10,3,80,17),feature('Support frame',5,27,22,25),feature('Control unit',40,30,30,20),feature('Battery cabinet',5,64,30,25),feature('Bicycle charging bays',45,62,50,30)]
        model='''The diagram illustrates the layout of a solar-powered shelter for charging bicycles. Overall, the structure combines a roof-mounted power collection section with equipment and charging spaces beneath it. The solar panels span the upper part of the shelter, while the battery cabinet and bicycle bays occupy the lower area.

The panels are positioned across most of the top of the diagram. A support frame is shown below them on the left-hand side. The control unit is located further towards the centre, slightly to the right of the frame. These elements form the upper and middle sections of the shelter, leaving the charging equipment at a lower level.

In the lower left-hand corner there is a battery cabinet, whereas the bicycle charging bays occupy a broader area on the right. The control unit is therefore above the bays and to the upper right of the cabinet. The drawing identifies the principal components and their relative locations, rather than specifying their electrical connections. It supplies no power rating, storage capacity or charging time. Consequently, the shelter can be described in terms of its arrangement, but the diagram alone cannot establish how quickly a bicycle would charge or how many bicycles could be charged simultaneously.'''
    chart={'type':'diagram','title':title,'layouts':[{'name':'Labelled schematic','features':items}],'source_note':note}
    return chart,model,'Sơ đồ cấu tạo thực hành; không chứng minh thông số kỹ thuật hay độ an toàn. Chỉ mô tả các bộ phận và vị trí tương đối thể hiện trên hình.\n'+'\n'.join(f['label'] for f in items)
