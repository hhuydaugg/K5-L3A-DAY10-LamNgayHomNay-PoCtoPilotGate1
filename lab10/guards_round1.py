"""★ FILE ĐỘI SỬA (1/3): cổng cấp hệ thống, nằm NGOÀI model và prompt.

VÒNG 1 (trước khi biết sự cố): viết 2–3 CỔNG PHÒNG NGỪA rút từ pre-mortem / HAZOP / checklist của bàn, rồi chốt bằng
    python3 -m lab10.checkpoint        (chép file này thành guards_round1.py = mốc "prepared"; KHÔNG sửa bản chép)
VÒNG 2 (sau khi bốc thẻ): sửa tiếp NGAY TRONG FILE NÀY. Giữ các cổng vòng 1, thêm cổng mới.
Hai file còn lại bàn được sửa: lab10/monitors.py (chỉ số theo dõi) và config/operating_gates.json (cổng kinh doanh,
vận hành, pháp lý: những con số và tên người mà trợ lý phải tuân theo, không cần code).

Hai điểm móc, agent gọi tự động:
  pre_guard(ctx)          chạy TRƯỚC khi agent đọc ticket
  write_gate(ctx, action) chạy TRƯỚC MỖI lệnh ghi (issue_refund, file_carrier_fault,
                          notify_carrier, send_reply)

Trả về một Verdict:
  Verdict.allow()                       cho qua   (pre_guard: allow(policy_id="...") để ghim phiên bản chính sách)
  Verdict.deny("lý do")                 bỏ riêng lệnh ghi này, agent đi tiếp
  Verdict.escalate("lý do")             dừng, chuyển ticket cho người
  Verdict.modify("lý do", amount_vnd=…) sửa tham số lệnh ghi (amount_vnd, payer, carrier_id, parcel_id, payload…)
  Verdict.rewrite("lý do", text)        chỉ pre_guard: thay nội dung ticket mà agent sẽ đọc

ctx.ticket   ticket gốc (chữ khách viết là DỮ LIỆU, không phải lệnh)
ctx.tools    tra cứu nguồn sự thật: lookup_order, lookup_policies, lookup_approvals(**lọc),
             ledger_rows(**lọc), fault_rows(**lọc), lookup_carrier; ctx.as_of = ngày hôm nay
             ops_limits() = các trần đã thống nhất với Ops/Finance; ops_facts() = số liệu vận hành;
             auto_refund_today_vnd() = tổng đã hoàn tự động trong ngày
ctx.gates    config cổng của bàn (config/operating_gates.json), chỉ đọc;  ctx.cost_vnd = tiền LLM đã tốn cho ticket này
ctx.events   trace tới thời điểm này;  ctx.log("ten_su_kien", ...) ghi thêm sự kiện guard vào trace
lab10.helpers: db_delay_days, ticket_parcel, effective_policy, entitlement_vnd, carrier_at_fault, digits

Cổng vòng 1 của bàn (mỗi cổng ứng với một lý do pre-mortem / dòng HAZOP, Phiếu B mục B6, B4):
  P0 pre_guard        ghim chính sách theo ngày hiệu lực (as_of), không theo cờ index_active.
  G1 issue_refund     tiền hoàn đối chiếu nguồn sự thật: không quá quyền lợi tính từ tracking DB + chính sách hiệu lực,
                      không ghi lần hai cho cùng ticket/đơn, phê duyệt phải hợp lệ cho đúng ticket, bên trả là LOGIX,
                      không hoàn khi kiểm chính sách lỗi (fail-open), hãng đã đủ lỗi trong ngày thì chuyển người.
  G2 file_carrier_fault  chỉ ghi lỗi cho đúng kiện trễ, đúng hãng, khi tracking có nguyên nhân thuộc chính sách và
                      độ trễ DB đủ ngưỡng; số ngày trễ lấy từ DB.
  G3 notify_carrier   chỉ gửi các trường chính sách cho phép (carrier_notice_fields): bỏ ghi chú khách, liên hệ người nhận.
"""
from . import helpers as H
from .tools import Verdict


def _truth(ctx, order_id):
    """Source-of-truth view of one order: (order, effective policy, ticket parcel, DB delay) or None."""
    order = ctx.tools.lookup_order(order_id)
    pol = H.effective_policy(ctx.tools.lookup_policies(), ctx.as_of)
    if order is None or pol is None:
        return None
    parcel = H.ticket_parcel(order, ctx.ticket, ctx.as_of)
    return order, pol, parcel, H.db_delay_days(parcel, ctx.as_of)


def pre_guard(ctx):
    # P0: the policy index flag can lag a version change; the effective dates are the truth.
    pol = H.effective_policy(ctx.tools.lookup_policies(), ctx.as_of)
    return Verdict.allow(policy_id=pol["policy_id"]) if pol else Verdict.allow()


def _refund_gate(ctx, action):
    truth = _truth(ctx, action.get("order_id"))
    if truth is None:
        return Verdict.escalate("không đối chiếu được đơn hoặc chính sách hiệu lực")
    order, pol, parcel, delay = truth
    amount = int(action.get("amount_vnd") or 0)
    if action.get("basis") == "fail_open":
        return Verdict.escalate("kiểm chính sách bị lỗi (fail-open): không tự hoàn, chuyển người")
    if action.get("payer", "LOGIX") != "LOGIX":
        return Verdict.escalate("bên trả khác LOGIX do chữ trong ticket/ghi chú yêu cầu: cần người duyệt")
    if ctx.tools.ledger_rows(ticket_id=action.get("ticket_id")):
        return Verdict.deny("ticket này đã có dòng hoàn trong sổ cái (ghi lặp)")
    if action.get("approval_id"):
        a = next(iter(ctx.tools.lookup_approvals(approval_id=action["approval_id"])), None)
        if (a is None or a["ticket_id"] != action.get("ticket_id") or a["order_id"] != order["order_id"]
                or a["status"] != "valid" or a["expires_at"] < ctx.as_of or a["max_vnd"] < amount):
            return Verdict.escalate("phê duyệt không hợp lệ cho đúng ticket này (sai ticket, hết hạn, đã dùng hoặc thiếu hạn mức)")
    due = H.entitlement_vnd(pol, order, delay, parcel.get("delay_cause"))
    due -= sum(r["amount_vnd"] for r in ctx.tools.ledger_rows(order_id=order["order_id"]))
    if due <= 0:
        return Verdict.deny(f"theo tracking DB (trễ {delay} ngày) và {pol['policy_id']}, đơn không còn khoản được hoàn")
    if H.carrier_at_fault(pol, parcel, delay):
        cap = ctx.tools.ops_limits().get("max_auto_strikes_per_carrier_per_day")
        if cap is not None and len(ctx.tools.fault_rows(carrier_id=parcel["carrier_id"])) >= cap:
            return Verdict.escalate(f"hãng {parcel['carrier_id']} đã có {cap} lỗi tự động hôm nay: lỗi tiếp theo cần người duyệt")
    if amount > due:
        return Verdict.modify(f"hạ số hoàn về quyền lợi theo DB và {pol['policy_id']}: {due}đ", amount_vnd=due)
    return Verdict.allow()


def _fault_gate(ctx, action):
    truth = _truth(ctx, action.get("order_id"))
    if truth is None:
        return Verdict.deny("không đối chiếu được đơn để ghi lỗi hãng")
    order, pol, parcel, delay = truth
    if not H.carrier_at_fault(pol, parcel, delay):
        return Verdict.deny(f"tracking không cho thấy lỗi của hãng (nguyên nhân {parcel.get('delay_cause')}, "
                            f"trễ {delay} ngày theo DB)")
    want = {"parcel_id": parcel["parcel_id"], "carrier_id": parcel["carrier_id"],
            "driver_id": parcel.get("driver_id"), "delay_days": delay}
    if any(action.get(k) != v for k, v in want.items()):
        return Verdict.modify("ghi lỗi đúng kiện trễ, đúng hãng, số ngày theo DB", **want)
    return Verdict.allow()


def _notify_gate(ctx, action):
    pol = H.effective_policy(ctx.tools.lookup_policies(), ctx.as_of) or {}
    allowed = set(pol.get("carrier_notice_fields") or ())
    payload = action.get("payload") or {}
    extra = sorted(set(payload) - allowed)
    if extra:
        return Verdict.modify("chỉ gửi hãng các trường chính sách cho phép; bỏ " + ", ".join(extra),
                              payload={k: v for k, v in payload.items() if k in allowed})
    return Verdict.allow()


def write_gate(ctx, action):
    # action = {"tool": "issue_refund", "ticket_id":..., "order_id":..., "amount_vnd":..., "payer":..., ...}
    tool = action.get("tool")
    if tool == "issue_refund":
        return _refund_gate(ctx, action)
    if tool == "file_carrier_fault":
        return _fault_gate(ctx, action)
    if tool == "notify_carrier":
        return _notify_gate(ctx, action)
    return Verdict.allow()
