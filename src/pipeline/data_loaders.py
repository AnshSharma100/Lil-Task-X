import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import pandas as pd


@dataclass
class Employee:
    name: str
    role: str
    experience_level: str
    skills: List[str]
    hourly_rate: float
    email: str

    @property
    def normalized_skills(self) -> List[str]:
        return [skill.strip().lower() for skill in self.skills]


@dataclass
class BudgetLine:
    resource: str
    value: str


@dataclass
class Budget:
    engineering_budget: float
    qa_budget: float
    cloud_budget: float
    licensing_budget: float
    gemini_available: bool
    gemini_monthly_cost: float
    firebase_monthly_cost: float
    security_budget: float
    training_budget: float
    contingency_reserve: float
    raw: List[BudgetLine]

    def as_dict(self) -> Dict[str, float]:
        total_budget = (
            self.engineering_budget
            + self.qa_budget
            + self.cloud_budget
            + self.licensing_budget
            + self.security_budget
            + self.training_budget
            + self.contingency_reserve
        )
        return {
            "engineering_budget": self.engineering_budget,
            "qa_budget": self.qa_budget,
            "cloud_budget": self.cloud_budget,
            "licensing_budget": self.licensing_budget,
            "gemini_available": self.gemini_available,
            "gemini_monthly_cost": self.gemini_monthly_cost,
            "firebase_monthly_cost": self.firebase_monthly_cost,
            "security_budget": self.security_budget,
            "training_budget": self.training_budget,
            "contingency_reserve": self.contingency_reserve,
            "total_budget_available": total_budget,
        }


def load_product_description(path: Path) -> str:
    text = path.read_text(encoding="utf-8").strip()
    return text


def load_people(path: Path) -> List[Employee]:
    df = pd.read_csv(path)
    employees: List[Employee] = []
    for row in df.itertuples(index=False):
        skills = str(row.Skills).split(",") if isinstance(row.Skills, str) else []
        employees.append(
            Employee(
                name=str(row.Name),
                role=str(row.Role),
                experience_level=str(row.Experience_Level),
                skills=skills,
                hourly_rate=float(row.Hourly_Rate_USD),
                email=str(row.Email),
            )
        )
    return employees


def load_budget(path: Path) -> Budget:
    df = pd.read_csv(path)
    raw_lines = [BudgetLine(resource=row.Resource, value=row.Value) for row in df.itertuples(index=False)]
    mapped: Dict[str, str] = {row.Resource: row.Value for row in df.itertuples(index=False)}
    return Budget(
        engineering_budget=float(mapped.get("Engineering Budget (USD)", 0)),
        qa_budget=float(mapped.get("QA Budget (USD)", 0)),
        cloud_budget=float(mapped.get("Cloud Services Budget (USD)", 0)),
        licensing_budget=float(mapped.get("Licensing & Tools Budget (USD)", 0)),
        gemini_available=str(mapped.get("Gemini API Available", "False")).lower() == "true",
        gemini_monthly_cost=float(mapped.get("Gemini API Monthly Cost (USD)", 0)),
        firebase_monthly_cost=float(mapped.get("Firebase Auth Monthly Cost (USD)", 0)),
        security_budget=float(mapped.get("Security/Compliance Budget (USD)", 0)),
        training_budget=float(mapped.get("Training & Upskilling Budget (USD)", 0)),
        contingency_reserve=float(mapped.get("Emergency Contingency Reserve (USD)", 0)),
        raw=raw_lines,
    )


def dump_json(path: Path, payload: Dict) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
