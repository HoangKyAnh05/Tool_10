# Codex Chat Gateway

Gateway dùng Codex App Server và phiên đăng nhập ChatGPT của Codex trên máy Windows. Chọn nguồn **Codex Chat** trong Cài đặt kết nối, nhập ID của chat riêng hoặc dùng chat gateway đã thiết lập trên máy. Mức suy nghĩ mặc định **Medium**, áp dụng cho tạo đề, chấm bài và chat API. Hạn mức tài khoản, model và ngữ cảnh vẫn áp dụng; key riêng của gateway không phải API key của OpenAI.

Ứng dụng không đặt giới hạn ký tự trả lời riêng. Chỉ lưu câu trả lời cuối khi lượt hoàn tất thành công; lượt trống, bị ngắt hay lỗi không được tính là thành công. Mọi yêu cầu chạy tuần tự trên một chat để giữ lịch sử. Sau khi khởi động lại, gateway tiếp tục đúng chat bằng `thread/resume`.

## Dùng trong app

Chọn Codex Chat → kiểm tra kết nối. Chat gateway phải chỉ có một tiến trình ghi; mở cùng chat để gửi trực tiếp trong Codex Desktop có thể gây xung đột. Dùng chat riêng cho API và xem lịch sử qua Hourly Coach. Khi tệp đăng nhập Codex thay đổi sau khi đổi tài khoản, gateway khởi động lại kết nối App Server trước yêu cầu kế tiếp và giữ chat riêng cùng mức Medium. Kiểm tra kết nối rồi thử một câu trả lời thật; online chỉ xác nhận bước nối, không chứng minh lượt tạo/chấm thành công. Nếu hết hạn mức hoặc auth lỗi, app lưu lỗi để thử lại.

Không cần key riêng `/ask` để tạo đề/chấm từ giao diện. Chỉ đặt key tối thiểu 16 ký tự khi muốn gọi gateway từ tool khác. Key lưu bằng DPAPI, ô trống giữ nguyên giá trị đã lưu.

## Gọi từ tool khác trên cùng máy

```javascript
async function askCodex(prompt, key, requestId, imagePath = "") {
  const response = await fetch("http://127.0.0.1:8766/ask", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${key}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      prompt,
      image_path: imagePath,
      request_id: requestId,
      timeout_seconds: 900
    }),
    signal: AbortSignal.timeout(960000)
  });
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || `HTTP ${response.status}`);
  return result.answer;
}
```

Lấy key từ cấu hình bí mật của tool, không hardcode hoặc ghi Authorization vào log. `image_path` là đường dẫn tuyệt đối trên máy gateway. Mỗi yêu cầu mới dùng `request_id` mới; giữ mã khi cần tra lỗi hoặc đọc lại kết quả. Cùng mã/nội dung đã hoàn tất trả đáp án lưu sẵn; mã đang chạy/thất bại hoặc trùng mã khác nội dung trả 409. Lỗi không tự gửi lại câu hỏi. Hết thời gian chờ sẽ ngắt đúng lượt do gateway tạo.

Server chỉ nghe localhost. Không có backend Render/cloud hay đường truy cập từ thiết bị khác trong bản này. Dữ liệu prompt/đáp án và cấu hình chat nằm trong `data/` và không được xuất bản cùng mã nguồn.

Tài liệu: [Codex App Server](https://learn.chatgpt.com/docs/app-server), [Đăng nhập](https://learn.chatgpt.com/docs/auth).
