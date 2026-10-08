"""Optional subprocess so transcription dependencies do not affect the tray app."""
import json
import sys
from faster_whisper import WhisperModel

if __name__=='__main__':
    model=WhisperModel(sys.argv[2],device='cpu',compute_type='int8',download_root=sys.argv[3])
    segments,info=model.transcribe(sys.argv[1],language='en',vad_filter=True,word_timestamps=True)
    parts=[]; words=[]
    for segment in segments:
        parts.append(segment.text.strip())
        for word in segment.words or []:
            words.append({'word':word.word,'start':round(word.start,2),'end':round(word.end,2)})
    if not parts: raise RuntimeError('Không nhận được lời nói.')
    duration=info.duration
    pauses=[round(words[i]['start']-words[i-1]['end'],2) for i in range(1,len(words)) if words[i]['start']-words[i-1]['end']>1.0]
    print(json.dumps({'text':' '.join(parts),'words':words,'duration_seconds':round(duration,1),
         'words_per_minute':round(len(words)*60/duration,1) if duration else None,
         'pauses_over_one_second':pauses,'limit':'ASR có thể chép sai. Tốc độ/pauses chỉ mô tả, không là điểm phát âm.'},ensure_ascii=True))
