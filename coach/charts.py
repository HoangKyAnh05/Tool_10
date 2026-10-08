"""Render charts from validated numeric data; no imaginary infographic values."""
import hashlib
import json
import math
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

COLORS=['#276658','#98b078','#cdab67','#8296ad']
FORMAT_TYPES=('bar','line','pie','table','process','map','mixed','diagram')


def validate_chart(chart):
    if not isinstance(chart,dict) or chart.get('type') not in FORMAT_TYPES:
        raise ValueError('Task 1 cần bar, line, pie, table, process, map, mixed hoặc diagram.')
    if not isinstance(chart.get('title'),str) or not chart['title'].strip() or len(chart['title'])>160:
        raise ValueError('Biểu đồ cần tiêu đề.')
    kind=chart['type']
    if kind=='mixed':
        panels=chart.get('panels')
        if not isinstance(panels,list) or len(panels)!=2 or len({p.get('type') for p in panels if isinstance(p,dict)})!=2:
            raise ValueError('Dạng kết hợp cần hai hình khác dạng.')
        for panel in panels:
            if not isinstance(panel,dict) or panel.get('type') not in ('bar','line','pie','table'):raise ValueError('Hình kết hợp cần dữ liệu số.')
            validate_chart(panel)
        return chart
    if kind=='process':
        stages=chart.get('stages')
        if not isinstance(stages,list) or not 4<=len(stages)<=10 or any(not isinstance(s,str) or not 8<=len(s)<=180 for s in stages):
            raise ValueError('Quy trình cần 4–10 bước cụ thể, có thứ tự.')
        if not isinstance(chart.get('cyclical',False),bool):raise ValueError('cyclical cần true/false.')
        return chart
    if kind in ('map','diagram'):
        layouts=chart.get('layouts')
        if not isinstance(layouts,list) or len(layouts)!=(2 if kind=='map' else 1):raise ValueError('Bản đồ cần hai thời điểm; sơ đồ thiết bị cần một hình.')
        for layout in layouts:
            if not isinstance(layout,dict) or not isinstance(layout.get('name'),str) or not layout['name'].strip():raise ValueError('Hình cần tên/thời điểm.')
            features=layout.get('features')
            if not isinstance(features,list) or not 3<=len(features)<=12:raise ValueError('Mỗi hình cần 3–12 chi tiết.')
            boxes=[]
            for f in features:
                if not isinstance(f,dict) or not isinstance(f.get('label'),str) or not 1<=len(f['label'])<=65:raise ValueError('Chi tiết cần nhãn ngắn.')
                if any(isinstance(f.get(k),bool) or not isinstance(f.get(k),(int,float)) or not math.isfinite(f[k]) for k in ('x','y','w','h')):raise ValueError('Tọa độ hình cần số hữu hạn.')
                if not (0<=f['x']<=100 and 0<=f['y']<=100 and 8<=f['w']<=100 and 8<=f['h']<=100 and f['x']+f['w']<=100 and f['y']+f['h']<=100):raise ValueError('Chi tiết hình phải nằm trong vùng 0–100.')
                box=(f['x'],f['y'],f['x']+f['w'],f['y']+f['h'])
                if any(box[0]<b[2] and box[2]>b[0] and box[1]<b[3] and box[3]>b[1] for b in boxes):raise ValueError('Các ô hình đang chồng nhau; sửa tọa độ.')
                boxes.append(box)
        return chart
    categories=chart.get('categories',[]);series=chart.get('series',[])
    if not 2<=len(categories)<=10 or any(not isinstance(c,str) or not c.strip() or len(c)>55 for c in categories):
        raise ValueError('Biểu đồ cần 2–10 nhãn hợp lệ.')
    if not 1<=len(series)<=4:
        raise ValueError('Biểu đồ cần 1–4 chuỗi số liệu.')
    for s in series:
        if not isinstance(s,dict) or not isinstance(s.get('name'),str) or not s['name'].strip() or len(s['name'])>60:
            raise ValueError('Chuỗi biểu đồ chưa có tên.')
        values=s.get('values',[])
        if len(values)!=len(categories) or any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not 0<=v<=1e8 for v in values):
            raise ValueError('Số liệu biểu đồ không khớp nhãn hoặc ngoài phạm vi.')
    if chart.get('unit')=='%' and any(v>100 for s in series for v in s['values']):
        raise ValueError('Tỷ lệ phần trăm trong biểu đồ phải từ 0 đến 100.')
    if kind=='pie' and (chart.get('unit')!='%' or any(abs(sum(s['values'])-100)>.05 for s in series)):
        raise ValueError('Mỗi biểu đồ tròn cần cơ cấu phần trăm tổng bằng 100.')
    return chart


def font(size,bold=False):
    path=Path('C:/Windows/Fonts')/('segoeuib.ttf' if bold else 'segoeui.ttf')
    return ImageFont.truetype(str(path),size) if path.exists() else ImageFont.load_default()


def render_chart(chart,folder):
    validate_chart(chart)
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    digest=hashlib.sha256(json.dumps({'renderer':2,'chart':chart},sort_keys=True).encode()).hexdigest()[:12]
    target=folder/f'chart-{digest}.png'
    if target.exists(): return target
    if chart['type'] not in ('bar','line'):return render_extended(chart,target,folder)
    im=Image.new('RGB',(1400,800),'#ffffff');d=ImageDraw.Draw(im)
    d.rounded_rectangle((20,20,1380,780),radius=22,fill='#fcfdf9',outline='#e2e8d9',width=2)
    title=chart['title']
    if d.textlength(title,font=font(29,True))>1250:
        titlefont=font(23,True)
    else:titlefont=font(29,True)
    d.text((70,54),title,fill='#304d37',font=titlefont)
    d.text((70,101),'IELTS ACADEMIC · WRITING TASK 1',fill='#93a483',font=font(15,True))
    legend_x=70
    for i,s in enumerate(chart['series']):
        d.rounded_rectangle((legend_x,147,legend_x+18,165),radius=3,fill=COLORS[i])
        d.text((legend_x+27,142),s['name'],fill='#657c58',font=font(20))
        legend_x+=int(d.textlength(s['name'],font=font(20)))+77
    left,right,top,bottom=110,1300,223,636
    unit=str(chart.get('unit',''))[:40]
    peak=max(v for s in chart['series'] for v in s['values'])
    if unit=='%':maximum=100
    elif peak==0:maximum=10
    else:
        magnitude=10**math.floor(math.log10(peak));maximum=math.ceil(peak/magnitude)*magnitude
        if maximum==peak:maximum*=1.1
    def y(v):return bottom-(v/maximum)*(bottom-top)
    d.text((left-44,190),unit or 'Value',fill='#839775',font=font(17))
    for i in range(6):
        value=maximum*i/5;yy=y(value)
        d.line((left,yy,right,yy),fill='#e6ebdf',width=1)
        label=f'{value:g}';length=d.textlength(label,font=font(17))
        d.text((left-16-length,yy-12),label,fill='#8c9e7d',font=font(17))
    n=len(chart['categories']);group=(right-left)/n
    for index,label in enumerate(chart['categories']):
        xx=left+group*(index+.5)
        # Split long labels instead of clipping them outside the chart.
        if d.textlength(label,font=font(20))>group-12:
            words=label.split();mid=max(1,len(words)//2);label=' '.join(words[:mid])+'\n'+' '.join(words[mid:])
        d.multiline_text((xx,bottom+20),label,fill='#657d57',font=font(20),anchor='ma',align='center',spacing=3)
    for i,s in enumerate(chart['series']):
        color=COLORS[i];count=len(chart['series']);points=[]
        width=min(60,group*.65/count)
        for j,value in enumerate(s['values']):
            center=left+group*(j+.5)
            if chart['type']=='bar':
                xx=center+(i-(count-1)/2)*(width+8)
                d.rounded_rectangle((xx-width/2,y(value),xx+width/2,bottom),radius=4,fill=color)
            else:
                xx=center;points.append((xx,y(value)))
            label=f'{value:g}'+('%' if unit=='%' else '')
            d.text((xx,y(value)-29),label,fill=color,font=font(17,True),anchor='ma')
        if points:
            d.line(points,fill=color,width=4)
            for x,yy in points:d.ellipse((x-6,yy-6,x+6,yy+6),fill=color)
    note=str(chart.get('source_note','Practice dataset · not a real-world statistical claim'))
    if d.textlength(note,font=font(15))>1240:note=note[:130]+'…'
    d.text((70,735),note,fill='#96a888',font=font(15))
    im.save(target,'PNG');return target


def wrapped(draw,text,box,size=22,bold=False):
    x,y,w,h=box
    for n in range(size,13,-1):
        face=font(n,bold);lines=[];current=''
        for word in str(text).split():
            trial=(current+' '+word).strip()
            if current and draw.textlength(trial,font=face)>w-20:lines.append(current);current=word
            else:current=trial
        if current:lines.append(current)
        if len(lines)*(n+7)<=h-10:break
    for i,line in enumerate(lines):draw.text((x+w/2,y+h/2+(i-(len(lines)-1)/2)*(n+7)),line,font=face,fill='#304d37',anchor='mm')


def arrow(draw,start,end):
    draw.line((*start,*end),fill='#276658',width=4)
    angle=math.atan2(end[1]-start[1],end[0]-start[0]);size=13
    points=[end,(end[0]-size*math.cos(angle-.5),end[1]-size*math.sin(angle-.5)),(end[0]-size*math.cos(angle+.5),end[1]-size*math.sin(angle+.5))]
    draw.polygon(points,fill='#276658')


def render_extended(chart,target,folder):
    kind=chart['type'];height=1100 if kind=='pie' and len(chart['series'])>2 else 1050 if kind=='process' and len(chart['stages'])>9 else 900
    im=Image.new('RGB',(1400,height),'white');d=ImageDraw.Draw(im)
    d.rounded_rectangle((20,20,1380,height-20),22,fill='#fcfdf9',outline='#dce5d8',width=2)
    wrapped(d,chart['title'],(55,35,1290,65),30,True)
    d.text((60,110),'IELTS ACADEMIC · WRITING TASK 1 · '+kind.upper(),font=font(17,True),fill='#6a815c')
    if kind=='mixed':
        images=[Image.open(render_chart(p,folder)).convert('RGB') for p in chart['panels']]
        im=Image.new('RGB',(1400,1810),'white');d=ImageDraw.Draw(im)
        wrapped(d,chart['title'],(20,0,1360,80),28,True)
        for i,pic in enumerate(images):
            pic.thumbnail((1360,815));im.paste(pic,((1400-pic.width)//2,85+i*850))
    elif kind=='table':
        rows=[['Category']+[s['name'] for s in chart['series']]]+[[label]+[f"{s['values'][i]:g}" for s in chart['series']] for i,label in enumerate(chart['categories'])]
        widths=[400]+[880/len(chart['series'])]*len(chart['series']);rowh=min(90,610/len(rows));y=185
        for ri,row in enumerate(rows):
            x=60
            for ci,label in enumerate(row):
                w=widths[ci];d.rectangle((x,y,x+w,y+rowh),fill='#e8efe1' if ri==0 else '#ffffff',outline='#cddbc5',width=2)
                wrapped(d,label,(x,y,w,rowh),24,ri==0);x+=w
            y+=rowh
        d.text((65,y+25),'Unit: '+str(chart.get('unit','')),font=font(20),fill='#657c58')
    elif kind=='pie':
        count=len(chart['series']);palette=['#276658','#98b078','#cdab67','#8296ad','#af8e9e','#7fa8a0','#ba9b7b','#727fa8','#c1ba78','#ad978c']
        for i,s in enumerate(chart['series']):
            col=i%2;row=i//2;size=280 if count>2 else 370;x=105+col*670;y=200+row*320
            d.text((x+size/2,y-35),s['name'],font=font(23,True),fill='#304d37',anchor='mm');angle=-90
            for j,v in enumerate(s['values']):
                end=angle+v*3.6;d.pieslice((x,y,x+size,y+size),angle,end,fill=palette[j],outline='white',width=3)
                if v:
                    mid=math.radians((angle+end)/2);d.text((x+size/2+size*.33*math.cos(mid),y+size/2+size*.33*math.sin(mid)),f'{v:g}%',font=font(18,True),fill='white',anchor='mm')
                angle=end
        yy=810 if count>2 else 660;xx=65
        for j,label in enumerate(chart['categories']):
            text=f'{label}';w=d.textlength(text,font=font(19))+50
            if xx+w>1320:yy+=34;xx=65
            d.rectangle((xx,yy,xx+17,yy+17),fill=palette[j]);d.text((xx+25,yy-3),text,font=font(19),fill='#304d37');xx+=w
    elif kind=='process':
        stages=chart['stages'];cols=3;positions=[]
        for i,s in enumerate(stages):
            row=i//cols;col=i%cols if row%2==0 else cols-1-i%cols
            x=85+col*425;y=200+row*180;positions.append((x,y))
            d.rounded_rectangle((x,y,x+360,y+120),18,fill='#eef4e9',outline='#83a376',width=2)
            wrapped(d,str(i+1)+'. '+s,(x+5,y+4,350,112),23)
        for (x,y),(nx,ny) in zip(positions,positions[1:]):
            if y==ny:arrow(d,(x+360 if nx>x else x,y+60),(nx if nx>x else nx+360,ny+60))
            else:arrow(d,(x+180,y+120),(nx+180,ny))
        if chart.get('cyclical'):d.text((70,height-95),'Cycle: the final stage returns to stage 1.',font=font(21,True),fill='#276658')
    elif kind in ('map','diagram'):
        count=len(chart['layouts']);width=600 if count==2 else 1220;layout_height=590
        for i,layout in enumerate(chart['layouts']):
            ox=65+i*670;oy=215
            d.text((ox+width/2,oy-35),layout['name'],font=font(24,True),fill='#304d37',anchor='mm')
            d.rectangle((ox,oy,ox+width,oy+layout_height),outline='#9ab18a',width=3)
            for f in layout['features']:
                x=ox+f['x']/100*width;y=oy+f['y']/100*layout_height;w=f['w']/100*width;h=f['h']/100*layout_height
                d.rounded_rectangle((x,y,x+w,y+h),8,fill='#edf3e7',outline='#718d61',width=2);wrapped(d,f['label'],(x,y,w,h),23)
            if kind=='map':d.text((ox+width-20,oy-70),'N ↑',font=font(20,True),fill='#276658',anchor='rm')
        d.text((65,820),'Schematic diagram · relative positions shown · not to scale',font=font(18),fill='#657c58')
    if kind!='mixed':
        note=str(chart.get('source_note','Original practice data; not official statistics.'))
        wrapped(d,note,(40,height-58,1320,33),16)
    im.save(target,'PNG');return target
