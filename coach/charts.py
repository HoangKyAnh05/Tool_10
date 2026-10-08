"""Render charts from validated numeric data; no imaginary infographic values."""
import hashlib
import json
import math
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

COLORS=['#276658','#98b078','#cdab67','#8296ad']


def validate_chart(chart):
    if not isinstance(chart,dict) or chart.get('type') not in ('bar','line'):
        raise ValueError('Task 1 cần chart type bar/line.')
    if not isinstance(chart.get('title'),str) or not chart['title'].strip():
        raise ValueError('Biểu đồ cần tiêu đề.')
    categories=chart.get('categories',[]);series=chart.get('series',[])
    if not 2<=len(categories)<=10 or any(not isinstance(c,str) or not c.strip() or len(c)>55 for c in categories):
        raise ValueError('Biểu đồ cần 2–10 nhãn hợp lệ.')
    if not 1<=len(series)<=4:
        raise ValueError('Biểu đồ cần 1–4 chuỗi số liệu.')
    for s in series:
        if not isinstance(s,dict) or not isinstance(s.get('name'),str) or not s['name'].strip():
            raise ValueError('Chuỗi biểu đồ chưa có tên.')
        values=s.get('values',[])
        if len(values)!=len(categories) or any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not 0<=v<=1e8 for v in values):
            raise ValueError('Số liệu biểu đồ không khớp nhãn hoặc ngoài phạm vi.')
    if chart.get('unit')=='%' and any(v>100 for s in series for v in s['values']):
        raise ValueError('Tỷ lệ phần trăm trong biểu đồ phải từ 0 đến 100.')
    return chart


def font(size,bold=False):
    path=Path('C:/Windows/Fonts')/('segoeuib.ttf' if bold else 'segoeui.ttf')
    return ImageFont.truetype(str(path),size) if path.exists() else ImageFont.load_default()


def render_chart(chart,folder):
    validate_chart(chart)
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    digest=hashlib.sha256(json.dumps(chart,sort_keys=True).encode()).hexdigest()[:12]
    target=folder/f'chart-{digest}.png'
    if target.exists(): return target
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
