# scripts/generate_json_schema.py
import json
from cogstaff.schema.profile_document import NeedAnalysisProfile, NeedAnalysisProfileDocument

def main() -> None:
    schema_profile = NeedAnalysisProfile.model_json_schema()
    schema_doc = NeedAnalysisProfileDocument.model_json_schema()

    with open("schemas/need_analysis_profile.schema.json", "w", encoding="utf-8") as f:
        json.dump(schema_profile, f, ensure_ascii=False, indent=2)

    with open("schemas/need_analysis_profile_document.schema.json", "w", encoding="utf-8") as f:
        json.dump(schema_doc, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
