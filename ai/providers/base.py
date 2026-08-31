from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type, TypeVar
from pydantic import BaseModel

# ميزة TypeVar للسماح بإرجاع كائنات Pydantic المحددة بدقة
T = TypeVar("T", bound=BaseModel)


class BaseAIProvider(ABC):
    """
    عقد مجرد (Abstract Interface) لجميع مزودي خدمات الذكاء الاصطناعي.
    
    الفائدة المعمارية:
    عزل محركات الهندسة والـ Domain تماماً عن المكتبات الخارجية (مثل google-genai).
    يمكن مستقبلاً التبديل إلى OpenAI, Anthropic, أو Local Models دون تعديل سطر كود واحد
    في المحركات الهندسية.
    """

    @abstractmethod
    async def generate_json(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        response_schema: Optional[Type[T]] = None,
        temperature: float = 0.1,
    ) -> Dict[str, Any]:
        """
        توليد استجابة بصيغة JSON بناءً على نص الموجه (Prompt).
        
        :param prompt: التعليمات أو النص المراد تحليله.
        :param system_instruction: تعليمات النظام لتوجيه سلوك AI.
        :param response_schema: نموذج Pydantic الاختياري للإلزام ببنية JSON محددة.
        :param temperature: درجة العشوائية (تُضبط افتراضياً على 0.1 لضمان استجابات هندسية دقيقة).
        :return: قاموس بيانات JSON أو Pydantic Model مقروء.
        """
        pass

    @abstractmethod
    async def analyze_vision(
        self,
        image_bytes: bytes,
        mime_type: str,
        prompt: str,
        system_instruction: Optional[str] = None,
        response_schema: Optional[Type[T]] = None,
        temperature: float = 0.1,
    ) -> Dict[str, Any]:
        """
        تحليل الوسائط البصرية (الصور والمخططات الهندسية) واستخراج بيانات مهيكلة منها.
        
        :param image_bytes: البايتات الخام للملف/الصورة.
        :param mime_type: نوع الامتداد (مثل: image/png, image/jpeg, application/pdf).
        :param prompt: التعليمات التفصيلية للمحلل البصري.
        :param system_instruction: تعليمات النظام الخاصة بالرؤية البصرية.
        :param response_schema: بنية الـ JSON المتوقعة للرد المكتشف.
        :param temperature: درجة العشوائية والضبط الموصى بها.
        :return: القاموس المستخرج الممثل للبيانات البصرية المكتشفة.
        """
        pass
