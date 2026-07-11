from parsers.ai_response_parser import AIResponseParser
from services.extraction_service import ExtractionService


def test_prescription_parser_wraps_single_prescription():
    result = AIResponseParser.validate(
        """
        {
          "patient_name": "Patient X",
          "age": "25",
          "gender": "male",
          "doctor_name": "Doctor A",
          "date": "2026-06-29",
          "medications": [{"drug": "Amoxicillin", "dosage": "500 mg"}]
        }
        """,
        "prescription",
        "image",
    )

    assert list(result.keys()) == ["prescriptions"]
    prescription = result["prescriptions"][0]
    assert prescription["patient_name"] == "Patient X"
    assert prescription["medications"][0]["medication_name"] == "Amoxicillin"


def test_prescription_parser_accepts_v2_fixed_schema():
    result = AIResponseParser.validate(
        """
        {
          "schema_version": "v2.0",
          "patient": { "name": "Patient X", "age": "25", "sex": "female" },
          "medications_facts": [
            {
              "verbatim_line": "Tab A 1-0-1 x 5 days",
              "drug": { "name": "Tab A" },
              "dose": { "amount": "", "unit": "" },
              "frequency": "Twice daily",
              "timing": "Morning and night",
              "duration": "5 days",
              "prn": false
            }
          ],
          "interpretation_inferences": { "working_diagnoses": ["Fever"] }
        }
        """,
        "prescription",
        "image",
    )

    assert result["schema_version"] == "v2.0"
    assert result["patient"]["name"] == "Patient X"
    assert result["document_facility"]["consultant"]["name"] == ""
    assert result["medications_facts"][0]["drug"]["name"] == "Tab A"


def test_merge_prescription_pages_by_patient_doctor_and_date():
    merged = ExtractionService._merge_prescriptions([
        {
            "patient_name": "Patient X",
            "age": "25",
            "gender": "female",
            "doctor_name": "Doctor A",
            "date": "2026-06-29",
            "medications": [{"medication_name": "Medicine 1"}],
            "uncertainty_notes": [],
        },
        {
            "patient_name": " patient x ",
            "age": "25",
            "gender": "M/F",
            "doctor_name": "doctor a",
            "date": None,
            "medications": [{"medication_name": "Medicine 2"}],
            "uncertainty_notes": ["page 2 unclear"],
        },
        {
            "patient_name": "Patient Y",
            "doctor_name": "Doctor B",
            "date": "2026-06-29",
            "medications": [{"medication_name": "Medicine 3"}],
            "uncertainty_notes": [],
        },
    ])

    assert len(merged) == 2
    assert [m["medication_name"] for m in merged[0]["medications"]] == [
        "Medicine 1",
        "Medicine 2",
    ]
    assert merged[0]["uncertainty_notes"] == ["page 2 unclear"]
    assert merged[1]["patient_name"] == "Patient Y"


def test_xray_image_parser_validates_expected_shape():
    result = AIResponseParser.validate(
        """
        {
          "body_part": "Chest",
          "findings": ["Clear lung fields"],
          "observations": ["No focal opacity"],
          "possible_abnormalities": [],
          "confidence": 0.91,
          "uncertainty_notes": ["Portable AP image"]
        }
        """,
        "xray",
        "image",
    )

    assert result["body_part"] == "Chest"
    assert result["confidence"] == 0.91


def test_xray_image_parser_accepts_v2_visual_understanding_schema():
    result = AIResponseParser.validate(
        """
        {
          "schema_version": "xray_v2.0",
          "patient": { "name": "Patient Y", "age": "40", "sex": "male" },
          "xray_study": { "body_part": "Chest", "view": "PA" },
          "visual_understanding": "Chest radiograph with both lung fields visible.",
          "findings_facts": ["No focal opacity"],
          "impression": ["No acute cardiopulmonary abnormality"]
        }
        """,
        "xray",
        "image",
    )

    assert result["schema_version"] == "xray_v2.0"
    assert result["patient"]["name"] == "Patient Y"
    assert result["xray_study"]["body_part"] == "Chest"
    assert result["visual_understanding"].startswith("Chest radiograph")


def test_xray_pdf_without_text_uses_image_prompt_type():
    assert ExtractionService._prompt_file_type("xray", "pdf", None) == "image"


def test_xray_pdf_with_text_uses_report_prompt_type():
    assert ExtractionService._prompt_file_type("xray", "pdf", "Findings text") == "pdf"


def test_merge_xray_image_pages_prefixes_page_context_and_averages_confidence():
    result = ExtractionService._merge_xray_image_pages([
        {
            "body_part": "Chest",
            "findings": ["Clear lungs"],
            "observations": ["No effusion"],
            "possible_abnormalities": [],
            "confidence": 0.8,
            "uncertainty_notes": [],
        },
        {
            "body_part": "Chest",
            "findings": ["Mild hyperinflation"],
            "observations": ["No effusion"],
            "possible_abnormalities": ["COPD changes"],
            "confidence": 0.6,
            "uncertainty_notes": ["Low inspiration"],
        },
    ])
    merged = result["xrays"][0]

    assert merged["body_part"] == "Chest"
    assert merged["findings"] == ["Clear lungs", "Mild hyperinflation"]
    assert merged["observations"] == ["No effusion"]
    assert merged["possible_abnormalities"] == ["COPD changes"]
    assert merged["confidence"] == 0.7


def test_merge_prescription_v2_pages_preserves_nested_medications_and_page_context():
    merged = ExtractionService._merge_prescription_v2_pages([
        AIResponseParser.validate(
            """
            {
              "schema_version": "v2.0",
              "patient": { "name": "Patient X", "age": "25" },
              "medications_facts": [
                { "verbatim_line": "Tab A 1-0-0", "drug": { "name": "Tab A" } }
              ],
              "uncertain_or_illegible_segments": []
            }
            """,
            "prescription",
            "image",
        ),
        AIResponseParser.validate(
            """
            {
              "schema_version": "v2.0",
              "patient": { "name": "Patient X" },
              "medications_facts": [
                { "verbatim_line": "Tab B 0-0-1", "drug": { "name": "Tab B" } }
              ],
              "uncertain_or_illegible_segments": ["dose unclear"]
            }
            """,
            "prescription",
            "image",
        ),
    ])

    assert merged["patient"]["name"] == "Patient X"
    assert merged["medications_facts"][0]["page"] == 1
    assert merged["medications_facts"][1]["page"] == 2
    assert merged["uncertain_or_illegible_segments"] == ["dose unclear"]


def test_merge_xray_v2_pages_combines_visual_understanding_and_findings():
    merged = ExtractionService._merge_xray_v2_pages([
        AIResponseParser.validate(
            """
            {
              "schema_version": "xray_v2.0",
              "xray_study": { "body_part": "Chest" },
              "visual_understanding": "Frontal chest image.",
              "findings_facts": ["Clear lungs"]
            }
            """,
            "xray",
            "image",
        ),
        AIResponseParser.validate(
            """
            {
              "schema_version": "xray_v2.0",
              "visual_understanding": "Second page contains report text.",
              "impression": ["No acute abnormality"]
            }
            """,
            "xray",
            "image",
        ),
    ])

    assert merged["xray_study"]["body_part"] == "Chest"
    assert merged["findings_facts"] == ["Clear lungs"]
    assert merged["impression"] == ["No acute abnormality"]
    assert merged["visual_understanding"] == "Frontal chest image.\nSecond page contains report text."


def test_group_prescription_v2_pages_by_patient_and_doctor():
    page_1 = AIResponseParser.validate(
        """
        {
          "schema_version": "v2.0",
          "patient": { "name": "Patient X" },
          "document_facility": { "consultant": { "name": "Doctor A" } },
          "medications_facts": [{ "drug": { "name": "Medicine 1" } }]
        }
        """,
        "prescription",
        "image",
    )
    page_2 = AIResponseParser.validate(
        """
        {
          "schema_version": "v2.0",
          "patient": { "name": "Patient X" },
          "document_facility": { "consultant": { "name": "Doctor A" } },
          "medications_facts": [{ "drug": { "name": "Medicine 2" } }]
        }
        """,
        "prescription",
        "image",
    )
    page_3 = AIResponseParser.validate(
        """
        {
          "schema_version": "v2.0",
          "patient": { "name": "Patient Y" },
          "document_facility": { "consultant": { "name": "Doctor B" } },
          "medications_facts": [{ "drug": { "name": "Medicine 3" } }]
        }
        """,
        "prescription",
        "image",
    )

    grouped = ExtractionService._group_prescription_v2_pages([page_1, page_2, page_3])

    assert len(grouped) == 2
    assert len(grouped[0]) == 2
    assert grouped[1][0]["patient"]["name"] == "Patient Y"


def test_merge_xray_image_pages_returns_xray_array_for_v2_groups():
    result = ExtractionService._merge_xray_image_pages([
        AIResponseParser.validate(
            """
            {
              "schema_version": "xray_v2.0",
              "patient": { "name": "Patient X" },
              "xray_study": { "body_part": "Chest" },
              "findings_facts": ["Clear lungs"]
            }
            """,
            "xray",
            "image",
        ),
        AIResponseParser.validate(
            """
            {
              "schema_version": "xray_v2.0",
              "patient": { "name": "Patient Y" },
              "xray_study": { "body_part": "Knee" },
              "findings_facts": ["No fracture"]
            }
            """,
            "xray",
            "image",
        ),
    ])

    assert len(result["xrays"]) == 2
    assert result["xrays"][0]["patient"]["name"] == "Patient X"
    assert result["xrays"][1]["xray_study"]["body_part"] == "Knee"


def test_validate_and_merge_lab_reports():
    page1 = AIResponseParser.validate(
        """
        {
          "schema_version": "lab_v1.0",
          "laboratory": { "name": "Lab A" },
          "patient": { "name": "John Doe", "age": "45" },
          "panels": [
            {
              "panel_name": "CBC",
              "tests": [
                { "test_name": "Hemoglobin", "result": "14.2", "unit": "g/dL", "flag": "Normal" }
              ]
            }
          ]
        }
        """,
        "lab_report",
        "image"
    )

    page2 = AIResponseParser.validate(
        """
        {
          "schema_version": "lab_v1.0",
          "laboratory": { "name": "Lab A" },
          "patient": { "name": "John Doe", "age": "45" },
          "panels": [
            {
              "panel_name": "CBC",
              "tests": [
                { "test_name": "WBC Count", "result": "11.5", "unit": "10^3/uL", "flag": "High" }
              ]
            },
            {
              "panel_name": "LFT",
              "tests": [
                { "test_name": "SGOT", "result": "35", "unit": "U/L", "flag": "Normal" }
              ]
            }
          ]
        }
        """,
        "lab_report",
        "image"
    )

    merged = ExtractionService._merge_lab_report_pages([page1, page2])

    assert merged["laboratory"]["name"] == "Lab A"
    assert merged["patient"]["name"] == "John Doe"
    assert len(merged["panels"]) == 2
    
    cbc_panel = next(p for p in merged["panels"] if p["panel_name"] == "CBC")
    lft_panel = next(p for p in merged["panels"] if p["panel_name"] == "LFT")
    
    assert len(cbc_panel["tests"]) == 2
    assert cbc_panel["tests"][0]["test_name"] == "Hemoglobin"
    assert cbc_panel["tests"][1]["test_name"] == "WBC Count"
    assert len(lft_panel["tests"]) == 1
    assert lft_panel["tests"][0]["test_name"] == "SGOT"

