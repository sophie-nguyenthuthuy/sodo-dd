import hashlib

from fastapi import APIRouter, File, UploadFile, status

from app.api.deps import ApiKeyDep, SessionDep
from app.core.exceptions import BadRequest, NotFound
from app.core.security import decrypt_field
from app.models import Certificate
from app.models.certificate import CertificateForm
from app.schemas.certificate import CertificateOut, CertificateParsed
from app.services.storage import upload_bytes

router = APIRouter(prefix="/certificates", tags=["certificates"])

ALLOWED = {"image/jpeg", "image/png", "image/tiff", "application/pdf"}
MAX_SIZE = 25 * 1024 * 1024  # 25 MB


@router.post("", response_model=CertificateOut, status_code=status.HTTP_201_CREATED)
async def upload_certificate(
    db: SessionDep,
    ak: ApiKeyDep,
    file: UploadFile = File(...),
) -> CertificateOut:
    if file.content_type not in ALLOWED:
        raise BadRequest(f"unsupported mime_type: {file.content_type}")
    body = await file.read()
    if len(body) > MAX_SIZE:
        raise BadRequest(f"file too large (>{MAX_SIZE} bytes)")
    if len(body) == 0:
        raise BadRequest("empty file")

    sha = hashlib.sha256(body).hexdigest()
    key = f"certificates/{ak.organization_id}/{sha[:2]}/{sha}"
    upload_bytes(key, body, content_type=file.content_type)

    cert = Certificate(
        id=Certificate.new_id(),
        organization_id=ak.organization_id,
        file_key=key,
        file_sha256=sha,
        file_size=len(body),
        mime_type=file.content_type,
        form=CertificateForm.UNKNOWN,
    )
    db.add(cert)
    db.commit()
    db.refresh(cert)
    return CertificateOut.model_validate(cert)


@router.get("/{certificate_id}", response_model=CertificateOut)
def get_certificate(certificate_id: str, db: SessionDep, ak: ApiKeyDep) -> CertificateOut:
    cert = db.get(Certificate, certificate_id)
    if cert is None or cert.organization_id != ak.organization_id:
        raise NotFound("certificate not found")
    out = CertificateOut.model_validate(cert)
    if cert.ocr_completed_at:
        out.parsed = CertificateParsed(
            form=cert.form,
            serial_number=decrypt_field(cert.serial_number_enc),
            book_number=decrypt_field(cert.book_number_enc),
            issued_at=cert.issued_at,
            issued_by=cert.issued_by,
            owner_name=decrypt_field(cert.owner_name_enc),
            owner_id=decrypt_field(cert.owner_id_enc),
            parcel_number=cert.parcel_number,
            sheet_number=cert.sheet_number,
            area_sqm=float(cert.area_sqm) if cert.area_sqm is not None else None,
            land_use_purpose=cert.land_use_purpose,
            land_use_term=cert.land_use_term,
            address=cert.address,
            ward=cert.ward,
            district=cert.district,
            province=cert.province,
        )
    return out
