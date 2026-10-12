"""Package quản lý và phân tích đa lĩnh vực pháp luật Việt Nam.

Bao gồm:
1. Hình sự (Criminal Law) - Hệ thống 7 hình phạt chính và 7 hình phạt bổ sung Điều 32 BLHS 2015.
2. Dân sự (Civil Law) - Tranh chấp hợp đồng, bồi thường thiệt hại ngoài hợp đồng, tài sản, thừa kế (BLDS 2015).
3. Hành chính (Administrative Law) - Tranh chấp với cơ quan nhà nước, khiếu nại, khiếu kiện hành chính (LTTHC 2015).
4. Thương mại (Commercial Law) - Tranh chấp kinh doanh thương mại, phạt vi phạm 8%, bồi thường, trọng tài (LTM 2005).
5. Kỷ luật & Lao động (Disciplinary & Labor Law) - Xử lý kỷ luật lao động (BLLĐ 2019) và kỷ luật cán bộ công chức (Luật CBCC).
6. Bộ phân loại & điều phối tự động (Dispatcher).
"""

from src.legal_domains.administrative import (
    AdministrativeActType,
    AdministrativeDisputeResolver,
    AdminResolutionStage,
    analyze_administrative_dispute,
)
from src.legal_domains.civil import (
    CivilDisputeResolver,
    CivilDisputeType,
    CivilResolutionMethod,
    analyze_civil_dispute,
)
from src.legal_domains.commercial import (
    CommercialDisputeResolver,
    CommercialDisputeType,
    CommercialRemedyType,
    analyze_commercial_dispute,
)
from src.legal_domains.criminal import (
    CriminalPenaltySystem,
    JudicialMeasureType,
    PrincipalPenaltyType,
    SupplementaryPenaltyType,
    analyze_criminal_penalties,
)
from src.legal_domains.disciplinary import (
    CivilServantDisciplineMeasure,
    DisciplinaryResolver,
    LaborDisciplineMeasure,
    analyze_disciplinary_matter,
)
from src.legal_domains.dispatcher import (
    LegalDomain,
    LegalDomainDispatcher,
    MultiDomainAnalysisResult,
)

__all__ = [
    "CriminalPenaltySystem",
    "PrincipalPenaltyType",
    "SupplementaryPenaltyType",
    "JudicialMeasureType",
    "analyze_criminal_penalties",
    "CivilDisputeResolver",
    "CivilDisputeType",
    "CivilResolutionMethod",
    "analyze_civil_dispute",
    "AdministrativeDisputeResolver",
    "AdministrativeActType",
    "AdminResolutionStage",
    "analyze_administrative_dispute",
    "CommercialDisputeResolver",
    "CommercialDisputeType",
    "CommercialRemedyType",
    "analyze_commercial_dispute",
    "DisciplinaryResolver",
    "LaborDisciplineMeasure",
    "CivilServantDisciplineMeasure",
    "analyze_disciplinary_matter",
    "LegalDomain",
    "LegalDomainDispatcher",
    "MultiDomainAnalysisResult",
]
