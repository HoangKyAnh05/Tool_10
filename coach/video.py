"""Run with the optional speech Python. Decode local videos without fetching URLs."""
import json,math,sys,wave
from fractions import Fraction
from pathlib import Path
import av


def extract(path,folder,count=12):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    with av.open(str(path)) as source:
        if not source.streams.video:raise ValueError('File không có hình video.')
        stream=source.streams.video[0]
        duration=float(stream.duration*stream.time_base) if stream.duration else float((source.duration or 0)/av.time_base)
        if not math.isfinite(duration) or not 0<duration<=1800:raise ValueError('Video cần có thời lượng xác định và tối đa 30 phút.')
        frames=[];seen=set();start=float((stream.start_time or 0)*stream.time_base)
        for i in range(count):
            target=max(0,(duration-.15)*i/(count-1))
            source.seek(int((start+target)/stream.time_base),stream=stream,backward=True)
            selected=None
            for frame in source.decode(stream):
                if frame.time is None:continue
                selected=frame
                if float(frame.time)-start>=target:break
            if selected is None:continue
            timestamp=round(float(selected.time)-start,3)
            if timestamp in seen:continue
            seen.add(timestamp)
            scale=min(1,1280/max(selected.width,selected.height))
            image=selected.reformat(width=max(1,int(selected.width*scale)),height=max(1,int(selected.height*scale)),format='rgb24')
            image.pts=None
            codec=av.CodecContext.create('png','w');codec.width=image.width;codec.height=image.height;codec.pix_fmt='rgb24';codec.time_base=Fraction(1,1)
            dest=folder/f'frame-{i+1:02d}.png'
            dest.write_bytes(b''.join(bytes(p) for p in list(codec.encode(image))+list(codec.encode(None))))
            frames.append({'path':str(dest.resolve()),'time_seconds':timestamp})
        info={'duration_seconds':round(duration,3),'width':stream.width,'height':stream.height,'frames':frames,'has_audio':bool(source.streams.audio)}
    if not frames:raise ValueError('Không trích được frame video.')
    if info['has_audio']:
        dest=folder/'audio.wav'
        with av.open(str(path)) as source,wave.open(str(dest),'wb') as output:
            output.setnchannels(1);output.setsampwidth(2);output.setframerate(16000)
            resampler=av.AudioResampler(format='s16',layout='mono',rate=16000)
            for frame in source.decode(audio=0):
                for chunk in resampler.resample(frame):output.writeframes(bytes(chunk.planes[0])[:chunk.samples*2])
            for chunk in resampler.resample(None):output.writeframes(bytes(chunk.planes[0])[:chunk.samples*2])
        info['audio_path']=str(dest.resolve())
    info['limits']='Phân tích các frame mẫu có timecode và transcript ASR. Không xem liên tục toàn bộ video, không nghe trực tiếp giọng/nhạc, không xác minh chuyển động giữa các frame hoặc số người xem.'
    return info


if __name__=='__main__':
    try:print(json.dumps(extract(sys.argv[1],sys.argv[2]),ensure_ascii=True))
    except Exception as error:
        print(json.dumps({'error':str(error)},ensure_ascii=True));raise SystemExit(1)
