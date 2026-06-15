Dự án này dựng cấu hình hệ thống LLM Inference với NVIDIA Dynamo trên hạ tầng K8s (3 node DGX-H200)

Rules:
- Khi yêu cầu dựng cho từng trường hợp, define tất cả các resource trong 1 file bằng NVIDIA Dynamo stack
- Luôn tìm thêm thông tin trước mỗi yêu cầu từ các nguồn NVIDIA (qua MCP nếu có thể), Context7, vLLM, Github
- Không được tự ý thực thi các yaml bằng kubectl nếu người dùng chưa cho phép
- Các yaml file viết ra phải ngắn gọn, đủ dùng, không dài dòng
- Chỉ comment với các trường hợp ngoại lệ và phải ghi rõ nguồn tham khảo tại nơi cần comment
- Endpoint benchmark cố định: `http://llm-bench-frontend:8000` (namespace `ai-dept-serving`). Dynamo: `metadata.name: llm-bench` + service key `frontend` → operator tạo Service `llm-bench-frontend` ([naming](https://github.com/ai-dynamo/dynamo/blob/main/deploy/operator/internal/dynamo/graph.go)). DeepSeek native: Service alias `llm-bench-frontend` trỏ router
- Quy tắc khi viết báo cáo phân tích kết quả benchmark:
    - Không báo cáo kịch bản benchmark
    - Tập trung làm rõ 2 khía cạnh quan trọng của hiệu năng: băng thông và độ trễ (TTFT, TPOT, E2E)
    - Các cấu hình cần so sánh nên sử dụng dạng bảng để so sánh, tính toán và báo cáo tỉ lệ lớn hơn / nhỏ hơn theo %
    - Phân tích sự ảnh hưởng của các cấu hình tới từng chỉ số
    - Cần nhúng ảnh / link từ kết quả benchmark để làm rõ thông tin
    - Cấu trúc tổng quan của tài liệu phân tích cần rõ ràng những ý sau:
        - các báo cáo khách quan dựa theo kết quả benchmark
        - nhận xét và phân tích từ các báo cáo khách quan đó
        - đưa ra lời khuyên nếu cần