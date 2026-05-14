from app.models.certificate import CertificateForm
from app.services.ocr.parser import CertificateParser

SAMPLE_2009 = """
CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM
Giấy chứng nhận quyền sử dụng đất, quyền sở hữu nhà ở và tài sản khác gắn liền với đất
Số phát hành: BU 837192
Số vào sổ cấp GCN: CS00123
Ông: NGUYỄN VĂN A
CCCD: 012345678901
Thửa đất số: 142
Tờ bản đồ số: 27
Diện tích: 78,5 m²
Mục đích sử dụng: Đất ở đô thị
Thời hạn: Lâu dài
Địa chỉ: Số 12 phố ABC, Phường Bồ Đề
Cơ quan cấp: UBND Quận Long Biên
Ngày cấp: 14/03/2018
Tỉnh Hà Nội
Quận Long Biên
Phường Bồ Đề
"""


def test_parser_detects_unified_2009():
    p = CertificateParser().parse(SAMPLE_2009)
    assert p.form == CertificateForm.UNIFIED_2009
    assert p.serial_number == "BU837192"
    assert p.book_number == "CS00123"
    assert p.owner_id == "012345678901"
    assert p.parcel_number == "142"
    assert p.sheet_number == "27"
    assert abs((p.area_sqm or 0) - 78.5) < 1e-6
    assert p.land_use_purpose and "Đất ở đô thị" in p.land_use_purpose
    assert p.issued_at == "14/03/2018"
    assert p.field_confidence["serial_number"] > 0.5


def test_parser_unknown_form():
    p = CertificateParser().parse("random text that mentions nothing relevant")
    assert p.form == CertificateForm.UNKNOWN
    assert p.serial_number is None
