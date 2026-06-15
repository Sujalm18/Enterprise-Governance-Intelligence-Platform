# Enterprise Regression Test Report

## Summary

- Total files: 90
- Total passed: 90
- Total failed: 0
- Pass percent: 100.00%

## Metrics

- Classification Accuracy: 100.00%
- Governance Detection Accuracy: 100.00%
- Governance Precision: 100.00%
- Governance Recall: 100.00%
- RAID Extraction Recall: 100.00%
- Escalation False Positive Rate: 0.00%
- Meeting Action Recall: 100.00%
- OCR Success Rate: 0.00%

## Top Failure Categories

- None

## Failed Documents

- None

## OCR Failure Cases

- None

## Scanned/Noisy PDFs Parsed Without OCR Fallback

- `data\regression\corpus\escalation_memos\escalation_memo_02.pdf`: pypdf extracted 4501 characters
- `data\regression\corpus\generic_business_docs\conflict_of_interest_policy_13.pdf`: pypdf extracted 8489 characters
- `data\regression\corpus\generic_business_docs\diversity_inclusion_policy_14.pdf`: pypdf extracted 8658 characters
- `data\regression\corpus\generic_business_docs\it_policy_08.pdf`: pypdf extracted 6855 characters
- `data\regression\corpus\generic_business_docs\marketing_strategy_05.pdf`: pypdf extracted 6375 characters
- `data\regression\corpus\generic_business_docs\procurement_policy_10.pdf`: pypdf extracted 8111 characters
- `data\regression\corpus\generic_business_docs\sales_brochure_06.pdf`: pypdf extracted 5878 characters
- `data\regression\corpus\generic_business_docs\social_media_policy_12.pdf`: pypdf extracted 7644 characters
- `data\regression\corpus\generic_business_docs\training_guide_07.pdf`: pypdf extracted 7833 characters
- `data\regression\corpus\governance_reports\steering_committee_report_04.pdf`: pypdf extracted 8837 characters
- `data\regression\corpus\meeting_minutes\meeting_minutes_hidden_risks_05.pdf`: pypdf extracted 3161 characters
- `data\regression\corpus\meeting_minutes\meeting_minutes_hidden_risks_06.pdf`: pypdf extracted 3003 characters
- `data\regression\corpus\meeting_minutes\meeting_minutes_hidden_risks_08.pdf`: pypdf extracted 3361 characters
- `data\regression\corpus\noisy_ocr_docs\noisy_ocr_01.pdf`: pypdf extracted 2602 characters
- `data\regression\corpus\noisy_ocr_docs\noisy_ocr_08.pdf`: pypdf extracted 4885 characters
- `data\regression\corpus\noisy_ocr_docs\noisy_ocr_10.pdf`: pypdf extracted 6850 characters
- `data\regression\corpus\project_status_reports\project_status_report_03_red.pdf`: pypdf extracted 4587 characters
- `data\regression\corpus\project_status_reports\project_status_report_04_vendor_delay.pdf`: pypdf extracted 4254 characters
- `data\regression\corpus\project_status_reports\project_status_report_10_erp_implementation.pdf`: pypdf extracted 5437 characters
- `data\regression\corpus\raid_registers\raid_register_09.pdf`: pypdf extracted 8047 characters

## False Escalation Cases

- None

## RAID Extraction Misses

- None

## Classification Confusion Summary

- expected `meeting_minutes` -> actual `meeting_minutes`: 25
- expected `generic_business_document` -> actual `generic_business_document`: 15
- expected `edge_case_document` -> actual `edge_case_document`: 10
- expected `noisy_ocr_document` -> actual `noisy_ocr_document`: 10
- expected `project_status_report` -> actual `project_status_report`: 10
- expected `raid_register` -> actual `raid_register`: 10
- expected `escalation_memo` -> actual `escalation_memo`: 5
- expected `governance_report` -> actual `governance_report`: 5

## Governance Confusion Summary

- expected `low` -> actual `low`: 40
- expected `high` -> actual `high`: 30
- expected `medium` -> actual `medium`: 20

## Extraction Summaries

- `data\regression\corpus\edge_cases\edge_case_01_very_short.txt`: pass=True, type=edge_case_document, relevance=medium, RAID=0, escalations=0, meeting_actions=0, OCR=False, time=0.06s
- `data\regression\corpus\edge_cases\edge_case_02_empty_minimal.txt`: pass=True, type=edge_case_document, relevance=medium, RAID=0, escalations=0, meeting_actions=0, OCR=False, time=0.00s
- `data\regression\corpus\edge_cases\edge_case_03_tables_charts.txt`: pass=True, type=edge_case_document, relevance=medium, RAID=0, escalations=0, meeting_actions=0, OCR=False, time=0.01s
- `data\regression\corpus\edge_cases\edge_case_04_handwritten_style.txt`: pass=True, type=edge_case_document, relevance=medium, RAID=4, escalations=0, meeting_actions=1, OCR=False, time=0.01s
- `data\regression\corpus\edge_cases\edge_case_05_mixed_languages.txt`: pass=True, type=edge_case_document, relevance=medium, RAID=1, escalations=0, meeting_actions=1, OCR=False, time=0.01s
- `data\regression\corpus\edge_cases\edge_case_06_scanned_style.txt`: pass=True, type=edge_case_document, relevance=medium, RAID=6, escalations=0, meeting_actions=6, OCR=False, time=0.02s
- `data\regression\corpus\edge_cases\edge_case_07_duplicate_content.txt`: pass=True, type=edge_case_document, relevance=medium, RAID=6, escalations=0, meeting_actions=6, OCR=False, time=0.01s
- `data\regression\corpus\edge_cases\edge_case_08_very_long.txt`: pass=True, type=edge_case_document, relevance=medium, RAID=0, escalations=0, meeting_actions=6, OCR=False, time=0.05s
- `data\regression\corpus\edge_cases\edge_case_09_nested_documents.txt`: pass=True, type=edge_case_document, relevance=medium, RAID=4, escalations=0, meeting_actions=2, OCR=False, time=0.01s
- `data\regression\corpus\edge_cases\edge_case_10_unusual_format.txt`: pass=True, type=edge_case_document, relevance=medium, RAID=0, escalations=0, meeting_actions=0, OCR=False, time=0.02s
- `data\regression\corpus\escalation_memos\escalation_memo_01.pdf`: pass=True, type=escalation_memo, relevance=high, RAID=8, escalations=1, meeting_actions=10, OCR=False, time=0.08s
- `data\regression\corpus\escalation_memos\escalation_memo_02.pdf`: pass=True, type=escalation_memo, relevance=high, RAID=8, escalations=0, meeting_actions=10, OCR=False, time=0.06s
- `data\regression\corpus\escalation_memos\escalation_memo_03.pdf`: pass=True, type=escalation_memo, relevance=high, RAID=8, escalations=0, meeting_actions=9, OCR=False, time=0.10s
- `data\regression\corpus\escalation_memos\escalation_memo_04.txt`: pass=True, type=escalation_memo, relevance=high, RAID=8, escalations=1, meeting_actions=10, OCR=False, time=0.04s
- `data\regression\corpus\escalation_memos\escalation_memo_05.txt`: pass=True, type=escalation_memo, relevance=high, RAID=8, escalations=0, meeting_actions=9, OCR=False, time=0.04s
- `data\regression\corpus\generic_business_docs\code_of_conduct_15.pdf`: pass=True, type=generic_business_document, relevance=low, RAID=0, escalations=0, meeting_actions=0, OCR=False, time=0.18s
- `data\regression\corpus\generic_business_docs\company_newsletter_04.pdf`: pass=True, type=generic_business_document, relevance=low, RAID=0, escalations=0, meeting_actions=0, OCR=False, time=0.11s
- `data\regression\corpus\generic_business_docs\conflict_of_interest_policy_13.pdf`: pass=True, type=generic_business_document, relevance=low, RAID=0, escalations=0, meeting_actions=0, OCR=False, time=0.14s
- `data\regression\corpus\generic_business_docs\diversity_inclusion_policy_14.pdf`: pass=True, type=generic_business_document, relevance=low, RAID=0, escalations=0, meeting_actions=0, OCR=False, time=0.10s
- `data\regression\corpus\generic_business_docs\employee_handbook_01.txt`: pass=True, type=generic_business_document, relevance=low, RAID=0, escalations=0, meeting_actions=0, OCR=False, time=0.03s
- `data\regression\corpus\generic_business_docs\facilities_policy_11.pdf`: pass=True, type=generic_business_document, relevance=low, RAID=0, escalations=0, meeting_actions=0, OCR=False, time=0.13s
- `data\regression\corpus\generic_business_docs\holiday_calendar_03.pdf`: pass=True, type=generic_business_document, relevance=low, RAID=0, escalations=0, meeting_actions=0, OCR=False, time=0.13s
- `data\regression\corpus\generic_business_docs\hr_policy_02.pdf`: pass=True, type=generic_business_document, relevance=low, RAID=0, escalations=0, meeting_actions=0, OCR=False, time=0.11s
- `data\regression\corpus\generic_business_docs\it_policy_08.pdf`: pass=True, type=generic_business_document, relevance=low, RAID=0, escalations=0, meeting_actions=0, OCR=False, time=0.08s
- `data\regression\corpus\generic_business_docs\marketing_strategy_05.pdf`: pass=True, type=generic_business_document, relevance=low, RAID=0, escalations=0, meeting_actions=0, OCR=False, time=0.09s
- `data\regression\corpus\generic_business_docs\procurement_policy_10.pdf`: pass=True, type=generic_business_document, relevance=low, RAID=0, escalations=0, meeting_actions=0, OCR=False, time=0.10s
- `data\regression\corpus\generic_business_docs\sales_brochure_06.pdf`: pass=True, type=generic_business_document, relevance=low, RAID=0, escalations=0, meeting_actions=0, OCR=False, time=0.13s
- `data\regression\corpus\generic_business_docs\social_media_policy_12.pdf`: pass=True, type=generic_business_document, relevance=low, RAID=0, escalations=0, meeting_actions=0, OCR=False, time=0.18s
- `data\regression\corpus\generic_business_docs\training_guide_07.pdf`: pass=True, type=generic_business_document, relevance=low, RAID=0, escalations=0, meeting_actions=0, OCR=False, time=0.15s
- `data\regression\corpus\generic_business_docs\travel_policy_09.txt`: pass=True, type=generic_business_document, relevance=low, RAID=0, escalations=0, meeting_actions=0, OCR=False, time=0.02s
- `data\regression\corpus\governance_reports\steering_committee_report_01.docx`: pass=True, type=governance_report, relevance=high, RAID=4, escalations=0, meeting_actions=3, OCR=False, time=0.06s
- `data\regression\corpus\governance_reports\steering_committee_report_02.docx`: pass=True, type=governance_report, relevance=high, RAID=9, escalations=1, meeting_actions=4, OCR=False, time=0.08s
- `data\regression\corpus\governance_reports\steering_committee_report_03.pdf`: pass=True, type=governance_report, relevance=high, RAID=7, escalations=2, meeting_actions=5, OCR=False, time=0.26s
- `data\regression\corpus\governance_reports\steering_committee_report_04.pdf`: pass=True, type=governance_report, relevance=high, RAID=9, escalations=0, meeting_actions=4, OCR=False, time=0.20s
- `data\regression\corpus\governance_reports\steering_committee_report_05.pdf`: pass=True, type=governance_report, relevance=high, RAID=9, escalations=0, meeting_actions=5, OCR=False, time=0.31s
- `data\regression\corpus\meeting_minutes\meeting_minutes_01.docx`: pass=True, type=meeting_minutes, relevance=low, RAID=0, escalations=0, meeting_actions=11, OCR=False, time=0.06s
- `data\regression\corpus\meeting_minutes\meeting_minutes_02.docx`: pass=True, type=meeting_minutes, relevance=low, RAID=0, escalations=0, meeting_actions=7, OCR=False, time=0.07s
- `data\regression\corpus\meeting_minutes\meeting_minutes_03.docx`: pass=True, type=meeting_minutes, relevance=low, RAID=0, escalations=0, meeting_actions=9, OCR=False, time=0.06s
- `data\regression\corpus\meeting_minutes\meeting_minutes_04.docx`: pass=True, type=meeting_minutes, relevance=low, RAID=0, escalations=0, meeting_actions=7, OCR=False, time=0.06s
- `data\regression\corpus\meeting_minutes\meeting_minutes_05.docx`: pass=True, type=meeting_minutes, relevance=low, RAID=0, escalations=0, meeting_actions=10, OCR=False, time=0.05s
- `data\regression\corpus\meeting_minutes\meeting_minutes_06.docx`: pass=True, type=meeting_minutes, relevance=low, RAID=0, escalations=0, meeting_actions=8, OCR=False, time=0.07s
- `data\regression\corpus\meeting_minutes\meeting_minutes_07.docx`: pass=True, type=meeting_minutes, relevance=low, RAID=0, escalations=0, meeting_actions=7, OCR=False, time=0.04s
- `data\regression\corpus\meeting_minutes\meeting_minutes_08.docx`: pass=True, type=meeting_minutes, relevance=low, RAID=0, escalations=0, meeting_actions=9, OCR=False, time=0.04s
- `data\regression\corpus\meeting_minutes\meeting_minutes_09.docx`: pass=True, type=meeting_minutes, relevance=low, RAID=0, escalations=0, meeting_actions=10, OCR=False, time=0.06s
- `data\regression\corpus\meeting_minutes\meeting_minutes_10.docx`: pass=True, type=meeting_minutes, relevance=low, RAID=0, escalations=0, meeting_actions=8, OCR=False, time=0.04s
- `data\regression\corpus\meeting_minutes\meeting_minutes_11.docx`: pass=True, type=meeting_minutes, relevance=low, RAID=0, escalations=0, meeting_actions=7, OCR=False, time=0.05s
- `data\regression\corpus\meeting_minutes\meeting_minutes_12.docx`: pass=True, type=meeting_minutes, relevance=low, RAID=0, escalations=0, meeting_actions=7, OCR=False, time=0.05s
- `data\regression\corpus\meeting_minutes\meeting_minutes_13.docx`: pass=True, type=meeting_minutes, relevance=low, RAID=0, escalations=0, meeting_actions=9, OCR=False, time=0.05s
- `data\regression\corpus\meeting_minutes\meeting_minutes_14.pdf`: pass=True, type=meeting_minutes, relevance=low, RAID=0, escalations=0, meeting_actions=5, OCR=False, time=0.12s
- `data\regression\corpus\meeting_minutes\meeting_minutes_15.txt`: pass=True, type=meeting_minutes, relevance=low, RAID=0, escalations=0, meeting_actions=7, OCR=False, time=0.01s
- `data\regression\corpus\meeting_minutes\meeting_minutes_hidden_risks_01.txt`: pass=True, type=meeting_minutes, relevance=low, RAID=0, escalations=0, meeting_actions=10, OCR=False, time=0.02s
- `data\regression\corpus\meeting_minutes\meeting_minutes_hidden_risks_02.pdf`: pass=True, type=meeting_minutes, relevance=low, RAID=0, escalations=0, meeting_actions=8, OCR=False, time=0.08s
- `data\regression\corpus\meeting_minutes\meeting_minutes_hidden_risks_03.txt`: pass=True, type=meeting_minutes, relevance=low, RAID=0, escalations=0, meeting_actions=9, OCR=False, time=0.02s
- `data\regression\corpus\meeting_minutes\meeting_minutes_hidden_risks_04.pdf`: pass=True, type=meeting_minutes, relevance=low, RAID=0, escalations=0, meeting_actions=10, OCR=False, time=0.08s
- `data\regression\corpus\meeting_minutes\meeting_minutes_hidden_risks_05.pdf`: pass=True, type=meeting_minutes, relevance=low, RAID=0, escalations=0, meeting_actions=6, OCR=False, time=0.07s
- `data\regression\corpus\meeting_minutes\meeting_minutes_hidden_risks_06.pdf`: pass=True, type=meeting_minutes, relevance=low, RAID=0, escalations=0, meeting_actions=10, OCR=False, time=0.05s
- `data\regression\corpus\meeting_minutes\meeting_minutes_hidden_risks_07.pdf`: pass=True, type=meeting_minutes, relevance=low, RAID=0, escalations=0, meeting_actions=9, OCR=False, time=0.06s
- `data\regression\corpus\meeting_minutes\meeting_minutes_hidden_risks_08.pdf`: pass=True, type=meeting_minutes, relevance=low, RAID=0, escalations=0, meeting_actions=10, OCR=False, time=0.06s
- `data\regression\corpus\meeting_minutes\meeting_minutes_hidden_risks_09.pdf`: pass=True, type=meeting_minutes, relevance=low, RAID=0, escalations=0, meeting_actions=10, OCR=False, time=0.07s
- `data\regression\corpus\meeting_minutes\meeting_minutes_hidden_risks_10.pdf`: pass=True, type=meeting_minutes, relevance=low, RAID=0, escalations=0, meeting_actions=8, OCR=False, time=0.07s
- `data\regression\corpus\noisy_ocr_docs\noisy_ocr_01.pdf`: pass=True, type=noisy_ocr_document, relevance=medium, RAID=5, escalations=0, meeting_actions=5, OCR=False, time=0.06s
- `data\regression\corpus\noisy_ocr_docs\noisy_ocr_02.pdf`: pass=True, type=noisy_ocr_document, relevance=medium, RAID=0, escalations=1, meeting_actions=6, OCR=False, time=0.11s
- `data\regression\corpus\noisy_ocr_docs\noisy_ocr_03.pdf`: pass=True, type=noisy_ocr_document, relevance=medium, RAID=6, escalations=0, meeting_actions=6, OCR=False, time=0.09s
- `data\regression\corpus\noisy_ocr_docs\noisy_ocr_04.txt`: pass=True, type=noisy_ocr_document, relevance=medium, RAID=1, escalations=0, meeting_actions=6, OCR=False, time=0.05s
- `data\regression\corpus\noisy_ocr_docs\noisy_ocr_05.pdf`: pass=True, type=noisy_ocr_document, relevance=medium, RAID=10, escalations=1, meeting_actions=1, OCR=False, time=0.12s
- `data\regression\corpus\noisy_ocr_docs\noisy_ocr_06.pdf`: pass=True, type=noisy_ocr_document, relevance=medium, RAID=0, escalations=0, meeting_actions=0, OCR=False, time=0.12s
- `data\regression\corpus\noisy_ocr_docs\noisy_ocr_07.pdf`: pass=True, type=noisy_ocr_document, relevance=medium, RAID=0, escalations=0, meeting_actions=1, OCR=False, time=0.14s
- `data\regression\corpus\noisy_ocr_docs\noisy_ocr_08.pdf`: pass=True, type=noisy_ocr_document, relevance=medium, RAID=0, escalations=0, meeting_actions=0, OCR=False, time=0.08s
- `data\regression\corpus\noisy_ocr_docs\noisy_ocr_09.txt`: pass=True, type=noisy_ocr_document, relevance=medium, RAID=0, escalations=0, meeting_actions=0, OCR=False, time=0.03s
- `data\regression\corpus\noisy_ocr_docs\noisy_ocr_10.pdf`: pass=True, type=noisy_ocr_document, relevance=medium, RAID=0, escalations=0, meeting_actions=1, OCR=False, time=0.09s
- `data\regression\corpus\project_status_reports\project_status_report_01_green.txt`: pass=True, type=project_status_report, relevance=high, RAID=6, escalations=0, meeting_actions=7, OCR=False, time=0.02s
- `data\regression\corpus\project_status_reports\project_status_report_02_amber.docx`: pass=True, type=project_status_report, relevance=high, RAID=7, escalations=2, meeting_actions=11, OCR=False, time=0.05s
- `data\regression\corpus\project_status_reports\project_status_report_03_red.pdf`: pass=True, type=project_status_report, relevance=high, RAID=9, escalations=2, meeting_actions=11, OCR=False, time=0.06s
- `data\regression\corpus\project_status_reports\project_status_report_04_vendor_delay.pdf`: pass=True, type=project_status_report, relevance=high, RAID=6, escalations=1, meeting_actions=9, OCR=False, time=0.07s
- `data\regression\corpus\project_status_reports\project_status_report_05_budget_overrun.docx`: pass=True, type=project_status_report, relevance=high, RAID=3, escalations=0, meeting_actions=12, OCR=False, time=0.08s
- `data\regression\corpus\project_status_reports\project_status_report_06_resource_shortage.txt`: pass=True, type=project_status_report, relevance=high, RAID=4, escalations=2, meeting_actions=10, OCR=False, time=0.03s
- `data\regression\corpus\project_status_reports\project_status_report_07_uat_issues.docx`: pass=True, type=project_status_report, relevance=high, RAID=8, escalations=0, meeting_actions=12, OCR=False, time=0.06s
- `data\regression\corpus\project_status_reports\project_status_report_08_infrastructure_dependency.docx`: pass=True, type=project_status_report, relevance=high, RAID=6, escalations=2, meeting_actions=12, OCR=False, time=0.07s
- `data\regression\corpus\project_status_reports\project_status_report_09_cloud_migration.docx`: pass=True, type=project_status_report, relevance=high, RAID=8, escalations=0, meeting_actions=11, OCR=False, time=0.08s
- `data\regression\corpus\project_status_reports\project_status_report_10_erp_implementation.pdf`: pass=True, type=project_status_report, relevance=high, RAID=8, escalations=0, meeting_actions=12, OCR=False, time=0.08s
- `data\regression\corpus\raid_registers\raid_register_01.xlsx`: pass=True, type=raid_register, relevance=high, RAID=12, escalations=0, meeting_actions=6, OCR=False, time=1.99s
- `data\regression\corpus\raid_registers\raid_register_02.xlsx`: pass=True, type=raid_register, relevance=high, RAID=14, escalations=2, meeting_actions=6, OCR=False, time=0.05s
- `data\regression\corpus\raid_registers\raid_register_03.xlsx`: pass=True, type=raid_register, relevance=high, RAID=18, escalations=0, meeting_actions=6, OCR=False, time=0.08s
- `data\regression\corpus\raid_registers\raid_register_04.xlsx`: pass=True, type=raid_register, relevance=high, RAID=14, escalations=0, meeting_actions=6, OCR=False, time=0.08s
- `data\regression\corpus\raid_registers\raid_register_05.xlsx`: pass=True, type=raid_register, relevance=high, RAID=17, escalations=0, meeting_actions=6, OCR=False, time=0.10s
- `data\regression\corpus\raid_registers\raid_register_06.xlsx`: pass=True, type=raid_register, relevance=high, RAID=18, escalations=0, meeting_actions=6, OCR=False, time=0.13s
- `data\regression\corpus\raid_registers\raid_register_07.xlsx`: pass=True, type=raid_register, relevance=high, RAID=18, escalations=0, meeting_actions=6, OCR=False, time=0.11s
- `data\regression\corpus\raid_registers\raid_register_08.xlsx`: pass=True, type=raid_register, relevance=high, RAID=17, escalations=0, meeting_actions=6, OCR=False, time=0.10s
- `data\regression\corpus\raid_registers\raid_register_09.pdf`: pass=True, type=raid_register, relevance=high, RAID=18, escalations=0, meeting_actions=6, OCR=False, time=0.24s
- `data\regression\corpus\raid_registers\raid_register_10.txt`: pass=True, type=raid_register, relevance=high, RAID=18, escalations=0, meeting_actions=6, OCR=False, time=0.18s
