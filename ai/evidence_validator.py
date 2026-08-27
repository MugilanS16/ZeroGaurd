from ai.amount_extractor import extract_claimed_amounts, extract_amount_from_image

def is_amount_matching(claimed: float, evidence_val: float, tolerance: float = 0.05) -> bool:
    """Checks if a claimed monetary amount matches an evidence amount within 5% tolerance or significant digits."""
    if claimed <= 0 or evidence_val <= 0:
        return False

    # 1. Percentage tolerance check (e.g., ±5%)
    diff_ratio = abs(claimed - evidence_val) / max(1.0, claimed)
    if diff_ratio <= tolerance:
        return True

    # 2. String integer representation match (e.g. 5000 vs 5000.0)
    claimed_str = str(int(round(claimed)))
    ev_str = str(int(round(evidence_val)))

    if claimed_str == ev_str or claimed_str in ev_str or ev_str in claimed_str:
        return True

    return False

def verify_amount_match(description_text: str, evidence_image_paths: list, answers_dict: dict = None) -> dict:
    """
    Cross-checks monetary amounts claimed in structured questionnaire fields or complaint text
    against OCR text extracted from uploaded evidence screenshots.
    
    Rules:
    - claimed_amounts is empty -> status = 'not_applicable' (non-financial complaint, skip check)
    - claimed_amounts matches an amount in OCR evidence -> status = 'verified'
    - claimed_amounts does NOT match evidence (wrong amount OR no amount in evidence) -> status = 'mismatch'
    """
    print(f"\n[DEBUG verify_amount_match] STARTING VERIFICATION")
    print(f"[DEBUG verify_amount_match] description_text='{description_text}'")
    print(f"[DEBUG verify_amount_match] answers_dict={answers_dict}")
    print(f"[DEBUG verify_amount_match] evidence_image_paths={evidence_image_paths}")

    claimed_amounts = extract_claimed_amounts(raw_description=description_text or '', answers_dict=answers_dict)
    print(f"[DEBUG verify_amount_match] claimed_amounts={claimed_amounts}")

    # 1. No amount claimed at all -> skip check (not_applicable)
    if not claimed_amounts:
        print(f"[DEBUG verify_amount_match] RESULT: status='not_applicable' (claimed_amounts is empty)")
        return {
            "status": "not_applicable",
            "claimed_amounts": [],
            "found_in_evidence": [],
            "matched_amount": None,
            "message": "No specific financial amount mentioned in description or questionnaire answers."
        }

    # 2. Extract OCR amounts from all uploaded evidence images
    found_in_evidence = set()
    for img_path in (evidence_image_paths or []):
        if img_path:
            img_amounts = extract_amount_from_image(str(img_path))
            for a in img_amounts:
                found_in_evidence.add(a)

    found_list = sorted(list(found_in_evidence))
    print(f"[DEBUG verify_amount_match] found_in_evidence={found_list}")

    # 3. Check for matches between claimed and evidence amounts
    matched_claimed = None
    for c_val in claimed_amounts:
        for e_val in found_list:
            if is_amount_matching(c_val, e_val):
                matched_claimed = c_val
                break
        if matched_claimed is not None:
            break

    # 4. Formulate Result: Case A (verified) vs Case B (mismatch - wrong amount or no amount in evidence)
    if matched_claimed is not None:
        result_data = {
            "status": "verified",
            "claimed_amounts": claimed_amounts,
            "found_in_evidence": found_list,
            "matched_amount": matched_claimed,
            "message": f"Claimed amount ₹{matched_claimed:,.0f} verified against evidence screenshot."
        }
    else:
        primary_claimed = claimed_amounts[0]
        result_data = {
            "status": "mismatch",
            "claimed_amounts": claimed_amounts,
            "found_in_evidence": found_list,
            "matched_amount": None,
            "message": f"⚠️ Your complaint mentions ₹{primary_claimed:,.0f}, but this amount was not found in your uploaded evidence. Please upload evidence that clearly shows this amount."
        }

    print(f"[DEBUG verify_amount_match] FINAL RETURN: status='{result_data['status']}', claimed_amounts={result_data['claimed_amounts']}, found_in_evidence={result_data['found_in_evidence']}")
    return result_data


