Dự án này dựng cấu hình hệ thống LLM Inference với NVIDIA Dynamo trên hạ tầng K8s (3 node DGX-H200)

Rules:
- Khi yêu cầu dựng cho từng trường hợp, define tất cả các resource trong 1 file bằng NVIDIA Dynamo stack
- Luôn tìm thêm thông tin trước mỗi yêu cầu từ các nguồn NVIDIA (qua MCP nếu có thể), Context7, vLLM, Github
- Không được tự ý thực thi các yaml bằng kubectl nếu người dùng chưa cho phép
- Các yaml file viết ra phải ngắn gọn, đủ dùng, không dài dòng
- Chỉ comment với các trường hợp ngoại lệ và phải ghi rõ nguồn tham khảo tại nơi cần comment