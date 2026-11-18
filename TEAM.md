# Team

## Thông tin nhóm

- Tên nhóm (`TenNhom`, không dấu, không khoảng trắng): LamNgayHomNay
- Lớp: `L3A`
- Repo của bàn: `K5-L3A-DAY10-LamNgayHomNay-PoCtoPilotGate1` (https://github.com/hhuydaugg/K5-L3A-DAY10-LamNgayHomNay-PoCtoPilotGate1)
- Thẻ sự cố đã bốc (S1–S8): (chưa bốc; thẻ phát ở phút 125)

## Thành viên

Họ tên đầy đủ và MSSV của **mọi** thành viên; thêm dòng nếu cần. Vai: Kỹ sư cổng · Sản phẩm và kinh doanh · Vận hành và pháp lý (README mục 3, phút 0–15).

| STT | Họ và tên | MSSV | Vai | Trưởng nhóm |
| --: | --------- | ---- | --- | :---------: |
|   1 | Nguyễn Hoàng Huy | 2A202603410 | Kỹ sư cổng · Sản phẩm và kinh doanh · Vận hành và pháp lý | ✔ |
|   2 |           |      |     |             |
|   3 |           |      |     |             |
|   4 |           |      |     |             |

Ghi `members` trong `submission/submission.json` theo dạng `"HoVaTen-MSSV"`, khớp bảng trên.

## Cá nhân

Mỗi thành viên tự viết một mục bên dưới (chép mẫu, đổi tiêu đề thành họ tên không dấu và MSSV, ví dụ `## NguyenVanAn-20241234`).

## NguyenHoangHuy-2A202603410

### Phần việc phụ trách

Cầm cả ba vai ở vòng 1:
- **Sản phẩm và kinh doanh:** câu 1.1, 1.5, 1.6 (Phiếu A); `config/acceptance_criteria.json`; câu 2.3, 2.9 (Phiếu B mục B3, B7.4); quyết định v1 (B8).
- **Kỹ sư cổng:** câu 1.3, 2.1, 2.2, 2.6–2.8; `lab10/guards.py`.
- **Vận hành và pháp lý:** câu 1.2, 1.4, 2.4, 2.10 (B4, B5, B7.5, B7.6); `config/operating_gates.json` mục `operations`, `legal`.

### Đóng góp cụ thể

- Viết và ký Bản tiêu chí trước lần chạy đầu tiên. Ngưỡng suy từ `ops_facts` / `ops_limits`: chi phí ≤ 6.000đ/ticket, ROI ≥ 0,5, chuyển người ≤ 0,35.
- Dò `T-002@55`: trợ lý tin "trễ 5 ngày" khách khai thay vì 2 ngày của DB.
- Viết cổng vòng 1:
  - P0 ghim chính sách theo ngày hiệu lực;
  - G1 đối chiếu tiền hoàn với tracking DB, chính sách, phê duyệt và sổ cái;
  - G2 chỉ ghi lỗi hãng đúng kiện có nguyên nhân;
  - G3 lọc trường gửi hãng.
- Điền cổng `business`, `operations`, `legal`; runbook 1–3 và giờ cao điểm.

### Bằng chứng

- Commit ký tiêu chí `19f6fe1`; chốt vòng 1 hash `a3e3f036`.
- Lần chạy:
  - `runs/R-base-before-20261118-231900-b45eeb` (base);
  - `runs/R-base-after-20261118-232133-b143c5` (cổng vòng 1);
  - `runs/R-base-prepared-20261118-232220-b143c5` (prepared);
  - `runs/R-base-after-20261118-232444-f43618` (thử 2 người trực).
- Phiếu A mục A1–A5, Phiếu B mục B0–B8.

### Exit ticket

(viết sau vòng 2)
