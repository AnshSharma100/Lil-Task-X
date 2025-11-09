import dataclasses
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


@dataclasses.dataclass
class PipelineConfig:
    product_description_path: Path
    developers_csv_path: Path
    testers_csv_path: Path
    budget_csv_path: Path
    outputs_dir: Path
    google_api_key_env: str = "GOOGLE_API_KEY"
    serpapi_api_key_env: str = "SERPAPI_KEY"
    exa_api_key_env: str = "EXA_API_KEY"
    gemini_model_env: str = "GEMINI_MODEL"
    gemini_fast_model_env: str = "GEMINI_FAST_MODEL"
    gemini_prd_model_env: str = "GEMINI_PRD_MODEL"
    default_gemini_model: str = "gemini-2.0-flash-exp"
    fast_gemini_model: str = "gemini-2.0-flash-exp"
    prd_gemini_model: str = "gemini-2.0-flash-exp"

    @classmethod
    def from_env(
        cls,
        base_dir: Path,
        outputs_dir: Optional[Path] = None,
        env_path: Optional[Path] = None,
    ) -> "PipelineConfig":
        if env_path is None:
            env_path = base_dir / ".env"
        if env_path.exists():
            load_dotenv(env_path)
        product_description_path = base_dir / "data" / "product_description.txt"
        developers_csv_path = base_dir / "data" / "developers_with_email.csv"
        testers_csv_path = base_dir / "data" / "testers_with_email.csv"
        budget_csv_path = base_dir / "data" / "company_budget.csv"
        outputs_dir = outputs_dir or base_dir / "outputs"
        outputs_dir.mkdir(parents=True, exist_ok=True)
        return cls(
            product_description_path=product_description_path,
            developers_csv_path=developers_csv_path,
            testers_csv_path=testers_csv_path,
            budget_csv_path=budget_csv_path,
            outputs_dir=outputs_dir,
        )

    @property
    def google_api_key(self) -> Optional[str]:
        return os.getenv(self.google_api_key_env)

    @property
    def serpapi_api_key(self) -> Optional[str]:
        return os.getenv(self.serpapi_api_key_env)

    @property
    def exa_api_key(self) -> Optional[str]:
        return os.getenv(self.exa_api_key_env)

    @property
    def resolved_gemini_model(self) -> str:
        """Primary Gemini model for agent tasks."""
        return os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")

    @property
    def resolved_fast_gemini_model(self) -> str:
        return os.getenv(self.gemini_fast_model_env, self.fast_gemini_model)

    @property
    def resolved_prd_gemini_model(self) -> str:
        return os.getenv(self.gemini_prd_model_env, self.prd_gemini_model)
