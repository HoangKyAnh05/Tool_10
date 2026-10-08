"""Reject reused question content, including exercises with a renamed title."""
import hashlib,json,re,unicodedata
from difflib import SequenceMatcher


def normalize(value):
    value=unicodedata.normalize('NFKC',str(value)).casefold()
    return ' '.join(re.findall(r'\w+',value))


def signature(data):
    fields={k:data.get(k) for k in ('objective','materials','writing_tasks','chart','speaking_tasks','retention_element','expertise_element') if data.get(k)}
    return normalize(json.dumps(fields,ensure_ascii=False,sort_keys=True))


def fingerprint(data):
    return hashlib.sha256(signature(data).encode('utf-8')).hexdigest()


def validate_novelty(store,data,category,skill,exclude_id=None):
    content=signature(data)
    for row in store.rows("SELECT id,body FROM assignments WHERE category=? AND (skill=? OR category<>'IELTS') AND archived=0",(category,skill)):
        if row['id']==exclude_id:continue
        old=json.loads(row['body'])
        old_content=signature(old)
        duplicate=content==old_content or SequenceMatcher(None,content,old_content).ratio()>.985
        if skill=='Writing' and old.get('writing_tasks'):
            a=normalize(data['writing_tasks'][1]);b=normalize(old['writing_tasks'][1])
            duplicate=duplicate or a==b or SequenceMatcher(None,a,b).ratio()>.94
            chart=lambda d:{k:d.get('chart',{}).get(k) for k in ('type','categories','series','unit','panels','stages','layouts')}
            duplicate=duplicate or chart(data)==chart(old)
        if skill=='Speaking' and old.get('speaking_tasks'):
            a=normalize(data['speaking_tasks']['part2']['cue_card']);b=normalize(old['speaking_tasks']['part2']['cue_card'])
            duplicate=duplicate or a==b or SequenceMatcher(None,a,b).ratio()>.96
            duplicate=duplicate or data['speaking_tasks']==old['speaking_tasks']
        if duplicate:raise ValueError('Nội dung đề trùng hoặc gần như trùng '+row['id']+'. Cần thay chủ đề, dữ liệu và yêu cầu, không chỉ đổi tiêu đề.')
    return data
