
let codexReply=null;
function codexSettings(){
 const c=state.settings;
 return `<div class="settings-box"><h2>${icon('spark')}Codex Chat · dùng phiên đăng nhập ChatGPT</h2>
 <p><strong>${health.model?`Đã nối ${esc(health.model)} · ${esc(health.reasoning_effort||"mặc định")}`:"Chưa xác nhận model"}</strong></p><p>Chat riêng do gateway quản lý, giữ model và dùng mức suy nghĩ bạn chọn bên dưới. Lưu nguyên câu trả lời và lịch sử; mỗi yêu cầu dùng hạn mức tài khoản Codex.</p>
 <form id="codex-form">
 <div class="field"><label for="codex-effort">Mức suy nghĩ của chat API</label><select id="codex-effort" name="codex_reasoning_effort">${[['','Theo chat'],['low','Low'],['medium','Medium'],['high','High'],['xhigh','Extra High']].map(([value,label])=>`<option value="${value}" ${(c.codex_reasoning_effort||'')===value?'selected':''}>${label}</option>`).join('')}</select><small>Áp dụng cho tạo đề, chấm bài và yêu cầu API tiếp theo; không thay đổi model.</small></div>
 <div class="field"><label for="codex-thread">Cuộc chat dành cho tool · Thread ID</label><input id="codex-thread" name="codex_thread_id" value="${esc(c.codex_thread_id)}" required><small>Đây là chat do gateway giữ quyền gửi tin. Chat mở trực tiếp trong cửa sổ Codex có thể đang được tiến trình khác giữ quyền ghi.</small></div>
 <div class="field"><label for="codex-key">Key riêng bạn tự đặt · tùy chọn<span>${c.codex_access_key_set?'✓ Đã lưu':'Chưa đặt'}</span></label><input id="codex-key" name="codex_access_key" type="password" autocomplete="new-password" minlength="16" placeholder="${c.codex_access_key_set?'Để trống để giữ key hiện tại':'Tự đặt ít nhất 16 ký tự nếu cần gọi API'}"><small>Chỉ cần cho tool khác gọi /ask. Nhận bài Telegram, chấm bài và chat ngay tại đây không cần key riêng.</small></div>
 <button class="btn primary" type="submit">Lưu Codex Chat & key riêng</button><button class="btn" type="button" data-action="health">Kiểm tra kết nối</button></form>
 <div class="field"><label>Endpoint gọi trực tiếp</label><code>POST http://127.0.0.1:8766/ask</code></div>
 <p>Header: Authorization: Bearer KEY_BẠN_ĐẶT<br>Body: {"prompt":"Câu hỏi của bạn", "image_path":""}</p>
 <form id="codex-chat-form"><div class="field"><label for="codex-prompt">Chat trực tiếp với Codex</label><textarea id="codex-prompt" name="prompt" required placeholder="Gửi yêu cầu đầy đủ của bạn…"></textarea></div><div class="field"><label for="codex-image">Ảnh kèm theo (tùy chọn)</label><input id="codex-image" type="file" accept=".png,.jpg,.jpeg,.webp"></div><button class="btn primary" type="submit">Gửi vào chat Codex</button></form>
 ${codexReply?`<div class="document"><h3>Đáp án đầy đủ · ${esc(codexReply.model||'Codex')}</h3><div class="doc-text">${esc(codexReply.answer||codexReply.error||'')}</div></div>`:''}
 <details class="answer-details"><summary>Lịch sử và log Codex gần đây</summary>${(state.codex_requests||[]).map(r=>`<div class="event"><div><button class="btn small" type="button" data-codex-request="${esc(r.id)}">Xem đầy đủ</button><a href="/api/codex/request?id=${encodeURIComponent(r.id)}" target="_blank" rel="noreferrer">Log JSON</a></div><span>${esc(r.status)} · ${esc(r.model||'')} · ${r.answer_chars||0} ký tự${r.error?'<br>'+esc(r.error):''}</span></div>`).join('')||'<p>Chưa có yêu cầu.</p>'}</details></div>`;
}
document.addEventListener('submit',async event=>{
 if(event.target.id!=='codex-form')return;
 event.preventDefault();const button=event.target.querySelector('button[type=submit]');button.disabled=true;
 try{await api('/api/codex/settings',Object.fromEntries(new FormData(event.target)));health=await api('/api/health');toast(health.online?'Đã nối chat Codex · '+health.model:'Đã lưu. '+(health.error||'Chưa kết nối được Codex.'),!health.online);await refresh(true);}
 catch(error){toast(error.message,true);}finally{if(button.isConnected)button.disabled=false;}
});
document.addEventListener('submit',async event=>{
 if(event.target.id!=='codex-chat-form')return;
 event.preventDefault();const form=event.target,button=form.querySelector('button[type=submit]');button.disabled=true;rendering=true;
 toast('Codex đang trả lời. Nội dung đầy đủ sẽ xuất hiện tại đây.');
 try{let image='';const file=form.querySelector('input[type=file]').files[0];
 if(file){if(file.size>20*1048576)throw new Error('Ảnh vượt 20 MB.');
 const data=await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(reader.result.split(',')[1]);reader.onerror=reject;reader.readAsDataURL(file);});
 image=(await api('/api/upload',{name:file.name,data})).path;}
 codexReply=await api('/api/codex/chat',{prompt:form.elements.prompt.value,image,request_id:crypto.randomUUID()});toast('Đã nhận toàn bộ đáp án Codex.');
 }catch(error){toast(error.message,true);}finally{rendering=false;await refresh(true);if(button.isConnected)button.disabled=false;}
});
document.addEventListener('click',async event=>{
 const button=event.target.closest('[data-codex-request]');if(!button)return;button.disabled=true;
 try{codexReply=await api('/api/codex/request?id='+encodeURIComponent(button.dataset.codexRequest));await refresh(true);}
 catch(error){toast(error.message,true);}finally{if(button.isConnected)button.disabled=false;}
});
