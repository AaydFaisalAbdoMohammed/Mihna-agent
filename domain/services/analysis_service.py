from typing import Any, Dict
from ai.facade import AIFacade
from domain.models.project import Project

# استدعاء المحركات الهندسية المتخصصة من مجلد engineering
from engineering.boq.engine import BOQEngine
from engineering.contracts.escrow import EscrowContractEngine
from engineering.architecture.engine import ArchitecturalEngine
from engineering.structural.preliminary import StructuralAnalysisEngine
from engineering.sustainability.engine import SustainabilityEngine
from engineering.blueprint.analyzer import BlueprintAnalyzer


class ProjectAnalysisDomainService:
    def __init__(self, ai_facade: AIFacade):
        self.ai_facade = ai_facade
        # تهيئة المحركات الهندسية المخصصة
        self.boq_engine = BOQEngine()
        self.escrow_engine = EscrowContractEngine()
        self.arch_engine = ArchitecturalEngine()
        self.structural_engine = StructuralAnalysisEngine()
        self.sustainability_engine = SustainabilityEngine()
        self.blueprint_analyzer = BlueprintAnalyzer()

    def execute_full_project_intake(self, project: Project, blueprint_bytes: bytes, mime_type: str) -> Dict[str, Any]:
        metadata = {
            "project_name": getattr(project, "name", "مشروع تجاري/سكني متكامل"),
            "land_area": getattr(project, "land_area", 0),
            "floors": getattr(project, "num_floors", 1),
            "budget": getattr(project, "budget", 0),
            "duration_days": getattr(project, "duration_days", 180),
            "building_type": getattr(project, "building_type", "Commercial/Residential"),
        }

        # 1. التحليل الأولي وتوليد الخطة عبر الذكاء الاصطناعي (Gemini Facade)
        ai_pipeline_res = self.ai_facade.process_full_engineering_pipeline(
            blueprint_bytes, mime_type, metadata
        )

        # 2. قراءة وتحليل المخططات المعمارية والتكعيب التلقائي
        blueprint_data = self.blueprint_analyzer.analyze_blueprint(blueprint_bytes, mime_type)
        boq_data = self.boq_engine.calculate_quantities_and_pricing(metadata, blueprint_data)

        # 3. توليد المخطط المعماري والمحاكاة الميدانية (Digital Twin)
        generative_arch = self.arch_engine.generate_layout_and_assumptions(metadata, blueprint_data)
        structural_analysis = self.structural_engine.evaluate_load_bearing(metadata)
        sustainability_metrics = self.sustainability_engine.analyze_efficiency(metadata)

        # 4. معالجة وتوليد عقد الضمان المشفر (ZKP Escrow & HMAC Signature)
        escrow_contract = self.escrow_engine.generate_escrow_contract(
            project_id=str(project.id),
            budget=metadata["budget"],
            payload=ai_pipeline_res
        )

        # 5. تجميع ومطابقة الأقسام الكاملة لتغذية كل تبويبات الواجهة (UI Tabs Payload)
        full_analysis_payload = {
            "project_id": str(project.id),
            "status": "success",
            # قسم الخطة التشغيلية والكوادر (Operational & Personnel Plan)
            "operational_plan": ai_pipeline_res.get("operational_plan", {}),
            "personnel_allocation": ai_pipeline_res.get("personnel", []),
            "work_breakdown_structure": ai_pipeline_res.get("wbs", []),
            "cost_time_breakdown": ai_pipeline_res.get("cost_allocation", {}),
            
            # قسم قراءة المخططات والتكعيب التلقائي (Blueprint & Auto BOQ)
            "blueprint_analysis": blueprint_data,
            "bill_of_quantities": boq_data,
            
            # قسم المخطط المعماري التوليدي (Generative Architectural Plan)
            "generative_architecture": generative_arch,
            
            # قسم المحاكاة الميدانية التوأم الرقمي (Field Simulation & Digital Twin)
            "digital_twin_simulation": {
                "structural_integrity": structural_analysis,
                "environmental_sustainability": sustainability_metrics,
                "simulation_status": "Active Twin Synced",
            },
            
            # قسم الضمان المشفر والعقود الذكية (ZKP Escrow Contract)
            "zkp_escrow_security": escrow_contract,
            
            # قسم التحليلات الهندسية والاتصالات والمرافق (Engineering Analytics & Utilities)
            "engineering_analytics": {
                "structural_loads": structural_analysis.get("loads", {}),
                "mep_connections": ai_pipeline_res.get("mep_details", {}),
                "sustainability_score": sustainability_metrics.get("score", 0),
            },
            
            # التوقيع الرقمي والبيانات الشاملة
            "digital_signature": escrow_contract.get("signature_hash", ""),
            "raw_ai_analysis": ai_pipeline_res
        }

        return full_analysis_payload
