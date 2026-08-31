#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
© 2026 PHOENIX & MIHNA AGENT PRO - ESCROW CONTRACT ENGINE
محرك عقود الضمان المالي والإفراج المشروط عن الدفعات للمشاريع الهندسية
===============================================================================
"""

import hashlib
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from engineering.shared.errors import CalculationError
from engineering.shared.validation import CommonValidator

logger = logging.getLogger(__name__)


class EscrowContractEngine:
    """
    محرك عقود الضمان وحسابات الإسكرو (Escrow Contract Engine).
    يدير عمليات التقييم التلقائي والإفراج عن المستحقات المالية بناءً على
    معايير جودة التنفيذ ونسبة الإنجاز الميداني بأسلوب غير معطل (Async).
    """

    MIN_QUALITY_THRESHOLD: float = 75.0      # الحد الأدنى لدرجة الجودة المقبولة (%)
    MIN_COMPLETION_THRESHOLD: float = 100.0  # نسبة الإنجاز المطلوبة للإفراج الكامل (%)

    @classmethod
    async def evaluate(
        cls, 
        quality_score: float, 
        completion_pct: float, 
        milestone_budget: float,
        milestone_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        تقييم مدى استحقاق الإفراج عن مبلغ المرحلة المالية وتوليد معرف التوثيق المشفر.

        :param quality_score: درجة جودة التنفيذ الهندسية (0 - 100).
        :param completion_pct: نسبة إنجاز أعمال المرحلة (0 - 100).
        :param milestone_budget: الميزانية المخصصة للمرحلة بالدولار الأمريكي.
        :param milestone_id: المعرف المرجعي للمرحلة المعتمدة.
        :return: قاموس يحتوي على حالة الدفعة (RELEASED/FROZEN)، المبلغ المفرج عنه، وتوقيع المعاملة.
        """
        try:
            # 1. التحقق الصارم من المدخلات عبر CommonValidator
            valid_quality = CommonValidator.validate_percentage(quality_score, "quality_score")
            valid_completion = CommonValidator.validate_percentage(completion_pct, "completion_pct")
            valid_budget = CommonValidator.validate_non_negative_number(milestone_budget, "milestone_budget")

            ref_id = milestone_id if milestone_id else "GENERIC_MILESTONE"

            # 2. التحقق من الشروط المعيارية للإفراج المالي
            if valid_quality < cls.MIN_QUALITY_THRESHOLD or valid_completion < cls.MIN_COMPLETION_THRESHOLD:
                reasons = []
                if valid_quality < cls.MIN_QUALITY_THRESHOLD:
                    reasons.append(f"مؤشر الجودة ({valid_quality}%) أقل من الحد الأدنى المطلوب ({cls.MIN_QUALITY_THRESHOLD}%).")
                if valid_completion < cls.MIN_COMPLETION_THRESHOLD:
                    reasons.append(f"نسبة الإنجاز ({valid_completion}%) لم تكتمل بنسبة 100%.")

                reason_str = " ".join(reasons)
                logger.warning(f"تم حجب الدفعة المالية للمرحلة '{ref_id}': {reason_str}")

                return {
                    "milestone_id": ref_id,
                    "status": "FROZEN",
                    "release_amount_usd": 0.0,
                    "held_amount_usd": round(valid_budget, 2),
                    "quality_score": valid_quality,
                    "completion_pct": valid_completion,
                    "reason": reason_str,
                    "evaluated_at": datetime.now(timezone.utc).isoformat()
                }

            # 3. توليد توقيع تشفير آمن للمعاملة المالية (SHA-256 Transaction Hash)
            utc_now = datetime.now(timezone.utc).isoformat()
            raw_tx_payload = f"{utc_now}_{ref_id}_{valid_budget}_ESCROW_RELEASE_SUCCESS"
            tx_hash = hashlib.sha256(raw_tx_payload.encode("utf-8")).hexdigest()

            logger.info(
                f"تم الإفراج المالي بنجاح للمرحلة '{ref_id}': "
                f"المبلغ {round(valid_budget, 2)}$، التوقيع {tx_hash[:10]}..."
            )

            return {
                "milestone_id": ref_id,
                "status": "RELEASED",
                "release_amount_usd": round(valid_budget, 2),
                "held_amount_usd": 0.0,
                "quality_score": valid_quality,
                "completion_pct": valid_completion,
                "tx_hash": tx_hash,
                "evaluated_at": utc_now,
                "reason": "تمت استيفاء جميع معايير الجودة والإنجاز الهندسي بنجاح."
            }

        except Exception as e:
            logger.exception("حدث خطأ أثناء تقييم عقد الإسكرو في EscrowContractEngine")
            raise CalculationError(
                message=f"فشل تقييم عقد الضمان والصفقة المالية: {str(e)}"
            )
