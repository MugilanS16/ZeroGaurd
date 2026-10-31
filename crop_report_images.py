import os
from PIL import Image

output_dir = os.path.join(os.getcwd(), "image", "report_figures")
os.makedirs(output_dir, exist_ok=True)

fig1_src = r"C:\Users\DR.MANN\.gemini\antigravity-ide\brain\cf907410-4993-493a-b605-02b14f8de59d\.user_uploaded\media_1790747036319.png"
grid_src = r"C:\Users\DR.MANN\.gemini\antigravity-ide\brain\cf907410-4993-493a-b605-02b14f8de59d\.user_uploaded\media_1790747023297.png"

# Fig 1: Save full image (crop small excess white borders if any)
img1 = Image.open(fig1_src)
img1.save(os.path.join(output_dir, "fig1_attack_vectors.png"))

grid = Image.open(grid_src)
W, H = grid.size

# Slicing bounding boxes (left, upper, right, lower)
# Row 1 (y: 0 to 215)
# Fig 2: x: 0 to 445, y: 0 to 215
fig2 = grid.crop((5, 10, 440, 215))
fig2.save(os.path.join(output_dir, "fig2_system_workflow.png"))

# Fig 3: x: 440 to 1018, y: 0 to 215
fig3 = grid.crop((440, 5, 1018, 215))
fig3.save(os.path.join(output_dir, "fig3_system_architecture.png"))

# Row 2 (y: 215 to 385)
# Fig 4: x: 5 to 340
fig4 = grid.crop((5, 220, 342, 385))
fig4.save(os.path.join(output_dir, "fig4_pii_redaction.png"))

# Fig 5: x: 342 to 675
fig5 = grid.crop((342, 220, 675, 385))
fig5.save(os.path.join(output_dir, "fig5_ocr_amount_verification.png"))

# Fig 6: x: 675 to 1018
fig6 = grid.crop((675, 220, 1018, 385))
fig6.save(os.path.join(output_dir, "fig6_semantic_relevance.png"))

# Row 3 (y: 385 to 545)
# Fig 7: x: 5 to 340
fig7 = grid.crop((5, 390, 342, 545))
fig7.save(os.path.join(output_dir, "fig7_audit_ledger.png"))

# Fig 8: x: 342 to 675
fig8 = grid.crop((342, 390, 675, 545))
fig8.save(os.path.join(output_dir, "fig8_user_interface.png"))

# Fig 9: x: 675 to 1018
fig9 = grid.crop((675, 390, 1018, 545))
fig9.save(os.path.join(output_dir, "fig9_i4c_classification.png"))

# Row 4 (y: 545 to 680)
# Fig 10: x: 5 to 340
fig10 = grid.crop((5, 550, 342, 678))
fig10.save(os.path.join(output_dir, "fig10_forensic_questioning.png"))

# Fig 11: x: 342 to 675
fig11 = grid.crop((342, 550, 675, 678))
fig11.save(os.path.join(output_dir, "fig11_evidence_preservation.png"))

# Fig 12: x: 675 to 1018
fig12 = grid.crop((675, 550, 1018, 678))
fig12.save(os.path.join(output_dir, "fig12_impact_outcomes.png"))

print(f"Successfully extracted all 12 figures to: {output_dir}")
