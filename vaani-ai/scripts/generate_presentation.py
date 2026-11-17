import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

ASSETS_DIR = r"C:\Users\Admin\Downloads\vaani-ai\vaani-ai\reports\assets"
CONF_MATRIX = r"C:\Users\Admin\Downloads\vaani-ai\vaani-ai\reports\confusion_matrix.png"
OUTPUT_PPTX = r"C:\Users\Admin\Downloads\vaani-ai\NLP_Major_Project_VaaniAI_Presentation.pptx"

# Color Palette (VaaniAI Dark Brand)
BG_COLOR = RGBColor(15, 23, 42)       # Slate 900
PANEL_COLOR = RGBColor(30, 41, 59)   # Slate 800
EMERALD = RGBColor(16, 185, 129)     # Emerald 500
EMERALD_DARK = RGBColor(5, 150, 105) # Emerald 600
TEXT_WHITE = RGBColor(248, 250, 252) # Slate 50
TEXT_MUTED = RGBColor(148, 163, 184) # Slate 400
ACCENT_BLUE = RGBColor(56, 189, 248) # Sky 400

def create_slide_with_bg(prs):
    slide_layout = prs.slide_layouts[6] # blank layout
    slide = prs.slides.add_slide(slide_layout)
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    bg.fill.solid()
    bg.fill.fore_color.rgb = BG_COLOR
    bg.line.fill.background()
    return slide

def add_header(slide, title_text, category="NLP MAJOR PROJECT"):
    # Category badge
    cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(8), Inches(0.35))
    tf_c = cat_box.text_frame
    tf_c.word_wrap = True
    p_c = tf_c.paragraphs[0]
    p_c.text = category.upper()
    p_c.font.size = Pt(10)
    p_c.font.bold = True
    p_c.font.color.rgb = EMERALD

    # Title
    title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.7), Inches(11), Inches(0.8))
    tf = title_box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = title_text
    p.font.size = Pt(24)
    p.font.bold = True
    p.font.color.rgb = TEXT_WHITE

def add_card(slide, left, top, width, height, title=None, bg_color=PANEL_COLOR):
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    card.fill.solid()
    card.fill.fore_color.rgb = bg_color
    card.line.color.rgb = RGBColor(51, 65, 85)
    card.line.width = Pt(1)
    
    if title:
        tb = slide.shapes.add_textbox(left + Inches(0.2), top + Inches(0.15), width - Inches(0.4), Inches(0.4))
        p = tb.text_frame.paragraphs[0]
        p.text = title
        p.font.size = Pt(14)
        p.font.bold = True
        p.font.color.rgb = EMERALD
    return card

def build_presentation():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    # -------------------------------------------------------------
    # SLIDE 1: Title Slide
    # -------------------------------------------------------------
    s1 = create_slide_with_bg(prs)
    
    # Hero Title box
    tbox = s1.shapes.add_textbox(Inches(1.0), Inches(1.2), Inches(11.333), Inches(2.5))
    tf = tbox.text_frame
    tf.word_wrap = True
    
    p_sub0 = tf.paragraphs[0]
    p_sub0.text = "NATURAL LANGUAGE PROCESSING (NLP) · MAJOR PROJECT"
    p_sub0.font.size = Pt(12)
    p_sub0.font.bold = True
    p_sub0.font.color.rgb = EMERALD
    p_sub0.space_after = Pt(10)
    
    p_title = tf.add_paragraph()
    p_title.text = "VAANI AI"
    p_title.font.size = Pt(44)
    p_title.font.bold = True
    p_title.font.color.rgb = TEXT_WHITE
    p_title.space_after = Pt(8)
    
    p_desc = tf.add_paragraph()
    p_desc.text = "AI-Powered Voice-to-Text Analysis and Multilingual Conversational Assistant"
    p_desc.font.size = Pt(20)
    p_desc.font.color.rgb = ACCENT_BLUE
    p_desc.space_after = Pt(16)
    
    p_detail = tf.add_paragraph()
    p_detail.text = "Full-Stack Multilingual NLP Pipeline · Transparent 7-Stage Insights · Local Offline-First Engine · Gemini Hybrid"
    p_detail.font.size = Pt(13)
    p_detail.font.color.rgb = TEXT_MUTED

    # Meta cards at bottom
    add_card(s1, Inches(1.0), Inches(4.5), Inches(5.4), Inches(2.2), title="PROJECT TEAM (GROUP OF 5)")
    c1_txt = s1.shapes.add_textbox(Inches(1.2), Inches(5.1), Inches(5.0), Inches(1.4))
    tf_c1 = c1_txt.text_frame
    tf_c1.word_wrap = True
    p = tf_c1.paragraphs[0]
    p.text = "• Yashvi (Lead Developer - NLP & ML Architecture)\n• Member 2 (Speech Processing & Native TTS Integration)\n• Member 3 (Frontend Engineering & Generative UI)\n• Member 4 (Data Engineering & Multi-Turn State)\n• Member 5 (Quality Assurance & Invariant Verification)"
    p.font.size = Pt(11)
    p.font.color.rgb = TEXT_WHITE

    add_card(s1, Inches(6.9), Inches(4.5), Inches(5.4), Inches(2.2), title="ACADEMIC SUPERVISION")
    c2_txt = s1.shapes.add_textbox(Inches(7.1), Inches(5.1), Inches(5.0), Inches(1.4))
    tf_c2 = c2_txt.text_frame
    tf_c2.word_wrap = True
    p = tf_c2.paragraphs[0]
    p.text = "• Faculty Guide: Prof. Sagar Jain\n• Department: Computer Science & Engineering\n• Course: Natural Language Processing (NLP)\n• Project Title #10: AI-Powered Voice Assistant\n• Academic Year: 2026-2027"
    p.font.size = Pt(11)
    p.font.color.rgb = TEXT_WHITE

    # -------------------------------------------------------------
    # SLIDE 2: Introduction & Motivation
    # -------------------------------------------------------------
    s2 = create_slide_with_bg(prs)
    add_header(s2, "Introduction & Project Motivation", "BACKGROUND")

    add_card(s2, Inches(0.8), Inches(1.7), Inches(5.6), Inches(5.2), title="THE MULTILINGUAL CHALLENGE")
    tb2_1 = s2.shapes.add_textbox(Inches(1.0), Inches(2.3), Inches(5.2), Inches(4.3))
    tf2_1 = tb2_1.text_frame
    tf2_1.word_wrap = True
    p = tf2_1.paragraphs[0]
    p.text = (
        "• India's Linguistic Landscape:\n"
        "  - 22 official scheduled languages across 12+ scripts.\n"
        "  - Heavy prevalence of Code-Switching (e.g. Hinglish).\n\n"
        "• Limitations of Existing Assistants (Siri / Alexa / Google):\n"
        "  - Closed 'Black Box': Tokenization, sentiment, and confidence scores are completely concealed.\n"
        "  - Network Dependency: No local command fallback when cloud connectivity fails.\n"
        "  - Pronunciation Distortion: Mixed-language answers (e.g. English phrase with Gujarati word) fail phonetically."
    )
    p.font.size = Pt(13)
    p.font.color.rgb = TEXT_WHITE

    add_card(s2, Inches(6.9), Inches(1.7), Inches(5.6), Inches(5.2), title="THE VAANI AI SOLUTION")
    tb2_2 = s2.shapes.add_textbox(Inches(7.1), Inches(2.3), Inches(5.2), Inches(4.3))
    tf2_2 = tb2_2.text_frame
    tf2_2.word_wrap = True
    p = tf2_2.paragraphs[0]
    p.text = (
        "• 100% Explainable NLP Dashboard:\n"
        "  - 7 live inspectable cards updating on every interaction.\n\n"
        "• Dual-Engine Architecture:\n"
        "  - High-confidence commands handled in <2 ms locally.\n"
        "  - Google Gemini hybrid fallback for open-ended queries.\n"
        "  - Complete offline fallback templates across 20 languages.\n\n"
        "• Segment-Level Target Voice Synthesis:\n"
        "  - Isolates translated terms and dynamically binds native regional voices (gu-IN, hi-IN, ta-IN, te-IN)."
    )
    p.font.size = Pt(13)
    p.font.color.rgb = TEXT_WHITE

    # -------------------------------------------------------------
    # SLIDE 3: Problem Statement & Objectives
    # -------------------------------------------------------------
    s3 = create_slide_with_bg(prs)
    add_header(s3, "Problem Statement & Key Objectives", "PROJECT FOUNDATION")

    add_card(s3, Inches(0.8), Inches(1.7), Inches(11.7), Inches(1.6), title="PROBLEM STATEMENT")
    tb3_ps = s3.shapes.add_textbox(Inches(1.0), Inches(2.2), Inches(11.3), Inches(0.9))
    tf = tb3_ps.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "To build a robust, accessible, and transparent voice-to-text multilingual conversational web application that combines speech transcription, multi-tier language detection, preprocessing, sentiment polarity scoring, intent classification, named entity recognition, machine translation, and native speech synthesis with zero-blackbox explainability."
    p.font.size = Pt(13)
    p.font.color.rgb = TEXT_WHITE

    add_card(s3, Inches(0.8), Inches(3.6), Inches(11.7), Inches(3.4), title="KEY DELIVERABLE OBJECTIVES")
    tb3_obj = s3.shapes.add_textbox(Inches(1.0), Inches(4.1), Inches(11.3), Inches(2.6))
    tf = tb3_obj.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = (
        "1. Real-Time Multilingual NLP: Support 20 core & extended languages with automatic script detection.\n"
        "2. 7-Stage NLP Dashboard: Live visual telemetry for LangID, Preprocessing, Sentiment, Intent, NER, Latency, and Translation.\n"
        "3. High-Accuracy Intent Model: ML pipeline trained on 14,800+ utterances with >= 93% test accuracy.\n"
        "4. Native TTS Speech Target: Accurate phonetic pronunciation of Indian languages (gu-IN, hi-IN, ta-IN, te-IN).\n"
        "5. WCAG AA Dual-Theme UI: Clean dark/light theme switching, independent panel scrolling, and mobile touch compliance."
    )
    p.font.size = Pt(13)
    p.font.color.rgb = TEXT_WHITE

    # -------------------------------------------------------------
    # SLIDE 4: Technologies Used
    # -------------------------------------------------------------
    s4 = create_slide_with_bg(prs)
    add_header(s4, "Technologies & System Tools", "TECHNICAL STACK")

    tech_cards = [
        ("Backend & Controller", "Python 3.13 & Flask", "REST API endpoints, session isolation, high-resolution latency profiling, and pipeline coordination.", Inches(0.8), Inches(1.7)),
        ("Machine Learning", "Scikit-Learn & Joblib", "TF-IDF word & char n-grams, Logistic Regression & Naive Bayes intent classifier (93.86% accuracy).", Inches(6.9), Inches(1.7)),
        ("Sentiment & NLP Rules", "VADER & Regex Engine", "VADER polarity scoring for English, custom negation window & valence scoring for Indic languages.", Inches(0.8), Inches(4.4)),
        ("Frontend & Speech", "Web Speech API & CSS3", "Client-side SpeechRecognition, SpeechSynthesis with regional voices, and WCAG AA dual-theme layout.", Inches(6.9), Inches(4.4)),
    ]
    for title, tech, desc, l, t in tech_cards:
        add_card(s4, l, t, Inches(5.6), Inches(2.4), title=title)
        tb = s4.shapes.add_textbox(l + Inches(0.2), t + Inches(0.6), Inches(5.2), Inches(1.6))
        tf = tb.text_frame
        tf.word_wrap = True
        p1 = tf.paragraphs[0]
        p1.text = tech
        p1.font.size = Pt(15)
        p1.font.bold = True
        p1.font.color.rgb = ACCENT_BLUE
        p1.space_after = Pt(4)
        p2 = tf.add_paragraph()
        p2.text = desc
        p2.font.size = Pt(11.5)
        p2.font.color.rgb = TEXT_WHITE

    # -------------------------------------------------------------
    # SLIDE 5: System Architecture & Data Flow
    # -------------------------------------------------------------
    s5 = create_slide_with_bg(prs)
    add_header(s5, "System Architecture & Staged Workflow", "ARCHITECTURE")

    add_card(s5, Inches(0.8), Inches(1.6), Inches(11.7), Inches(5.3), title="END-TO-END PIPELINE ARCHITECTURE")
    tb5 = s5.shapes.add_textbox(Inches(1.0), Inches(2.2), Inches(11.3), Inches(4.5))
    tf = tb5.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = (
        "[1. Voice / Text Input]  ──▶  Web Speech API / Composer Input\n"
        "         │\n"
        "[2. Language Identification] ──▶ Unicode Script Detection / Lexicon Trigrams (20 Languages)\n"
        "         │\n"
        "[3. Preprocessing & Normalization] ──▶ 60+ Contraction Expansion / Stopword Removal / Stemming\n"
        "         │\n"
        "[4. Sentiment Analysis] ──▶ VADER (English) + Multilingual Negation Valence Engine [-1.0 to +1.0]\n"
        "         │\n"
        "[5. Intent Classification & NER] ──▶ 24-Class TF-IDF Classifier (P(sum)=1.0) + Entity Extraction\n"
        "         │\n"
        "[6. Hybrid Conversational Router]\n"
        "         ├──▶ High Confidence Command (<2 ms) ──▶ Local Python Template Engine\n"
        "         ├──▶ Open-Ended / General Knowledge ──▶ Google Gemini Hybrid Fallback\n"
        "         └──▶ Network Disruption / Offline  ──▶ Multilingual Offline Fallback Templates\n"
        "         │\n"
        "[7. Translation & Native TTS] ──▶ Multi-Tier Translation + Isolated Voice Target (gu-IN, hi-IN, etc.)\n"
        "         │\n"
        "[8. Real-Time Telemetry Dashboard] ──▶ All 7 Cards Rendered Simultaneously in Dual Themes"
    )
    p.font.size = Pt(13)
    p.font.name = "Consolas"
    p.font.color.rgb = TEXT_WHITE

    # -------------------------------------------------------------
    # SLIDE 6: All 7 NLP Pipeline Stages Overview
    # -------------------------------------------------------------
    s6 = create_slide_with_bg(prs)
    add_header(s6, "Overview of All 7 NLP Transparency Stages", "NLP PIPELINE")

    stages = [
        ("1. LangID", "Unicode script detection & confidence scoring across 20 languages."),
        ("2. Preprocessing", "Contraction expansion ('I'm' -> 'I am'), Unicode NFC, stopword removal."),
        ("3. Sentiment", "Compound valence bounded [-1, +1], finite positive/neutral/negative %."),
        ("4. Intent Classification", "Calibrated ML argmax invariant; probabilities across classes sum to 1.0."),
        ("5. Named Entity (NER)", "Extracts Person, Location, Organization, Date, and Currency chips."),
        ("6. Latency & Engine", "High-resolution ms latency accounting for Local NLP, Chatbot, & Translation."),
        ("7. Translation & TTS", "Multi-tier translation routing with native voice binding (gu-IN, hi-IN, ta-IN)."),
    ]
    for idx, (st_name, st_desc) in enumerate(stages):
        top_y = Inches(1.7 + idx * 0.75)
        add_card(s6, Inches(0.8), top_y, Inches(11.7), Inches(0.65))
        tb = s6.shapes.add_textbox(Inches(1.0), top_y + Inches(0.08), Inches(11.3), Inches(0.45))
        p = tb.text_frame.paragraphs[0]
        r1 = p.add_run()
        r1.text = f"CARD {idx+1}: {st_name.upper()}  ──  "
        r1.font.bold = True
        r1.font.size = Pt(12)
        r1.font.color.rgb = EMERALD
        r2 = p.add_run()
        r2.text = st_desc
        r2.font.size = Pt(12)
        r2.font.color.rgb = TEXT_WHITE

    # -------------------------------------------------------------
    # SLIDE 7: Pipeline Cards 1 & 2 (Screenshots)
    # -------------------------------------------------------------
    s7 = create_slide_with_bg(prs)
    add_header(s7, "Pipeline Cards 1 & 2: Language ID & Preprocessing", "NLP STAGES")

    add_card(s7, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.3), title="CARD 1: LANGUAGE IDENTIFICATION")
    c1_img = os.path.join(ASSETS_DIR, "card1_lang_id.png")
    if os.path.exists(c1_img):
        s7.shapes.add_picture(c1_img, Inches(1.0), Inches(2.2), Inches(5.2), Inches(4.3))

    add_card(s7, Inches(6.9), Inches(1.6), Inches(5.6), Inches(5.3), title="CARD 2: PREPROCESSING & NORMALIZATION")
    c2_img = os.path.join(ASSETS_DIR, "card2_preprocessing.png")
    if os.path.exists(c2_img):
        s7.shapes.add_picture(c2_img, Inches(7.1), Inches(2.2), Inches(5.2), Inches(4.3))

    # -------------------------------------------------------------
    # SLIDE 8: Pipeline Cards 3 & 4 (Screenshots)
    # -------------------------------------------------------------
    s8 = create_slide_with_bg(prs)
    add_header(s8, "Pipeline Cards 3 & 4: Sentiment & Intent Classification", "NLP STAGES")

    add_card(s8, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.3), title="CARD 3: SENTIMENT & POLARITY")
    c3_img = os.path.join(ASSETS_DIR, "card3_sentiment.png")
    if os.path.exists(c3_img):
        s8.shapes.add_picture(c3_img, Inches(1.0), Inches(2.2), Inches(5.2), Inches(4.3))

    add_card(s8, Inches(6.9), Inches(1.6), Inches(5.6), Inches(5.3), title="CARD 4: INTENT CLASSIFICATION")
    c4_img = os.path.join(ASSETS_DIR, "card4_intent.png")
    if os.path.exists(c4_img):
        s8.shapes.add_picture(c4_img, Inches(7.1), Inches(2.2), Inches(5.2), Inches(4.3))

    # -------------------------------------------------------------
    # SLIDE 9: Pipeline Cards 5, 6 & 7 (Screenshots)
    # -------------------------------------------------------------
    s9 = create_slide_with_bg(prs)
    add_header(s9, "Pipeline Cards 5, 6 & 7: NER, Latency & Translation", "NLP STAGES")

    add_card(s9, Inches(0.8), Inches(1.6), Inches(3.7), Inches(5.3), title="CARD 5: NER")
    c5_img = os.path.join(ASSETS_DIR, "card5_ner.png")
    if os.path.exists(c5_img):
        s9.shapes.add_picture(c5_img, Inches(0.95), Inches(2.2), Inches(3.4), Inches(4.3))

    add_card(s9, Inches(4.8), Inches(1.6), Inches(3.7), Inches(5.3), title="CARD 6: LATENCY")
    c6_img = os.path.join(ASSETS_DIR, "card6_latency.png")
    if os.path.exists(c6_img):
        s9.shapes.add_picture(c6_img, Inches(4.95), Inches(2.2), Inches(3.4), Inches(4.3))

    add_card(s9, Inches(8.8), Inches(1.6), Inches(3.7), Inches(5.3), title="CARD 7: TRANSLATION")
    c7_img = os.path.join(ASSETS_DIR, "card7_translation.png")
    if os.path.exists(c7_img):
        s9.shapes.add_picture(c7_img, Inches(8.95), Inches(2.2), Inches(3.4), Inches(4.3))

    # -------------------------------------------------------------
    # SLIDE 10: Working Application - Dark Theme
    # -------------------------------------------------------------
    s10 = create_slide_with_bg(prs)
    add_header(s10, "Working Application: Dark Theme Full View", "LIVE APPLICATION")

    dark_full = os.path.join(ASSETS_DIR, "app_dark_theme_full.png")
    if os.path.exists(dark_full):
        s10.shapes.add_picture(dark_full, Inches(1.2), Inches(1.6), Inches(10.9), Inches(5.4))

    # -------------------------------------------------------------
    # SLIDE 11: Working Application - Light Theme
    # -------------------------------------------------------------
    s11 = create_slide_with_bg(prs)
    add_header(s11, "Working Application: Light Theme Full View", "LIVE APPLICATION")

    light_full = os.path.join(ASSETS_DIR, "app_light_theme_full.png")
    if os.path.exists(light_full):
        s11.shapes.add_picture(light_full, Inches(1.2), Inches(1.6), Inches(10.9), Inches(5.4))

    # -------------------------------------------------------------
    # SLIDE 12: Mobile Responsive Interface
    # -------------------------------------------------------------
    s12 = create_slide_with_bg(prs)
    add_header(s12, "Mobile Responsive Interface (375px Viewport)", "RESPONSIVENESS")

    mob1 = os.path.join(ASSETS_DIR, "mobile_chat_dark.png")
    if os.path.exists(mob1):
        s12.shapes.add_picture(mob1, Inches(1.5), Inches(1.6), Inches(2.8), Inches(5.4))

    mob2 = os.path.join(ASSETS_DIR, "mobile_insights_dark.png")
    if os.path.exists(mob2):
        s12.shapes.add_picture(mob2, Inches(5.0), Inches(1.6), Inches(2.8), Inches(5.4))

    add_card(s12, Inches(8.4), Inches(1.6), Inches(4.1), Inches(5.4), title="MOBILE OPTIMIZATIONS")
    tb12 = s12.shapes.add_textbox(Inches(8.6), Inches(2.2), Inches(3.7), Inches(4.4))
    tf12 = tb12.text_frame
    tf12.word_wrap = True
    p = tf12.paragraphs[0]
    p.text = (
        "• Mobile Tab Switcher:\n"
        "  - Dedicated '💬 Chat' and '🧠 NLP Insights' view toggles.\n\n"
        "• Touch Target Accessibility:\n"
        "  - Mic button: 44px x 44px\n"
        "  - Send button: 44px height\n"
        "  - Text input: min-height 44px\n\n"
        "• Responsive 1-Column Stack:\n"
        "  - Controls row stacks in clean logical order: I speak -> Reply in -> Translate -> Checkboxes -> New Chat."
    )
    p.font.size = Pt(13)
    p.font.color.rgb = TEXT_WHITE

    # -------------------------------------------------------------
    # SLIDE 13: Model Training & Confusion Matrix
    # -------------------------------------------------------------
    s13 = create_slide_with_bg(prs)
    add_header(s13, "Machine Learning Training & Confusion Matrix", "MODEL EVALUATION")

    if os.path.exists(CONF_MATRIX):
        s13.shapes.add_picture(CONF_MATRIX, Inches(0.8), Inches(1.6), Inches(6.8), Inches(5.4))

    add_card(s13, Inches(7.9), Inches(1.6), Inches(4.6), Inches(5.4), title="EVALUATION METRICS")
    tb13 = s13.shapes.add_textbox(Inches(8.1), Inches(2.2), Inches(4.2), Inches(4.5))
    tf13 = tb13.text_frame
    tf13.word_wrap = True
    p = tf13.paragraphs[0]
    p.text = (
        "• Training Corpus Size:\n"
        "  - 10,451 Training samples\n"
        "  - 1,872 Validation samples\n"
        "  - 2,555 Unseen Test samples\n\n"
        "• Champion Model Results:\n"
        "  - Overall Accuracy: 93.86%\n"
        "  - Macro F1-Score: 82.99%\n"
        "  - Inference Latency: < 1.5 ms\n\n"
        "• Robust Invariants:\n"
        "  - Probability Normalization: Sum strictly equals 1.0.\n"
        "  - Argmax Consistency: Top-ranked alternative equals prediction."
    )
    p.font.size = Pt(13)
    p.font.color.rgb = TEXT_WHITE

    # -------------------------------------------------------------
    # SLIDE 14: System Testing & Invariant Verification
    # -------------------------------------------------------------
    s14 = create_slide_with_bg(prs)
    add_header(s14, "Testing, Verification & Bug Fixes", "QUALITY ASSURANCE")

    tests = [
        ("Relative Date Handling", "Added multilingual date parsing. Accurately handles 'which date is tomorrow' (18 Nov), 'which day is tomorrow' (Wednesday), and Asia/Kolkata vs UTC 00:30 IST rollover."),
        ("Translation & Speech Fixes", "Resolved translation identity no-op. Implemented isolated target-language TTS binding (gu-IN, hi-IN, ta-IN, te-IN) for accurate native pronunciation."),
        ("Contraction Expansion & Stopwords", "Complete 60+ English contraction expansion dictionary ('I'm' -> 'I am'). Verified 'without_stopwords' strictly excludes language stopwords across 50+ sentences."),
        ("Zero-Division Sentiment Safety", "Fixed all zero-denominator cases in regional sentiment. Compound score strictly bounded in [-1.0, 1.0]; components are finite and sum to 100%."),
    ]
    for idx, (t_title, t_desc) in enumerate(tests):
        top_y = Inches(1.7 + idx * 1.3)
        add_card(s14, Inches(0.8), top_y, Inches(11.7), Inches(1.15), title=t_title)
        tb = s14.shapes.add_textbox(Inches(1.0), top_y + Inches(0.45), Inches(11.3), Inches(0.6))
        p = tb.text_frame.paragraphs[0]
        p.text = t_desc
        p.font.size = Pt(12.5)
        p.font.color.rgb = TEXT_WHITE

    # -------------------------------------------------------------
    # SLIDE 15: Conclusion & Future Scope
    # -------------------------------------------------------------
    s15 = create_slide_with_bg(prs)
    add_header(s15, "Conclusion & Future Research Directions", "SUMMARY")

    add_card(s15, Inches(0.8), Inches(1.7), Inches(5.6), Inches(5.2), title="PROJECT ACHIEVEMENTS")
    tb15_1 = s15.shapes.add_textbox(Inches(1.0), Inches(2.3), Inches(5.2), Inches(4.3))
    tf15_1 = tb15_1.text_frame
    tf15_1.word_wrap = True
    p = tf15_1.paragraphs[0]
    p.text = (
        "• Successfully Delivered:\n"
        "  - Complete working multilingual voice assistant across 20 languages.\n"
        "  - Real-time 7-card transparent NLP dashboard.\n"
        "  - 93.86% calibrated intent classification model.\n"
        "  - Native regional speech pronunciation (gu-IN, hi-IN, etc.).\n"
        "  - 100% test pass rate across unit, integration, and UI verification suites.\n\n"
        "• Production Deployment:\n"
        "  - Live local execution on http://127.0.0.1:5000.\n"
        "  - WCAG AA accessibility in both Light and Dark themes."
    )
    p.font.size = Pt(13)
    p.font.color.rgb = TEXT_WHITE

    add_card(s15, Inches(6.9), Inches(1.7), Inches(5.6), Inches(5.2), title="FUTURE SCOPE")
    tb15_2 = s15.shapes.add_textbox(Inches(7.1), Inches(2.3), Inches(5.2), Inches(4.3))
    tf15_2 = tb15_2.text_frame
    tf15_2.word_wrap = True
    p = tf15_2.paragraphs[0]
    p.text = (
        "• On-Device Offline Speech Transcription:\n"
        "  - Integrate quantized Whisper (Whisper.tflite) for zero-network speech-to-text.\n\n"
        "• Voice Emotion & Prosody:\n"
        "  - Modulate synthesis pitch, tempo, and warmth based on detected user sentiment.\n\n"
        "• Embedded IoT Deployment:\n"
        "  - Port lightweight local engine to Raspberry Pi smart speaker devices."
    )
    p.font.size = Pt(13)
    p.font.color.rgb = TEXT_WHITE

    # -------------------------------------------------------------
    # SLIDE 16: Q&A / Thank You
    # -------------------------------------------------------------
    s16 = create_slide_with_bg(prs)
    
    # Center Card
    add_card(s16, Inches(2.5), Inches(1.8), Inches(8.333), Inches(4.0))
    tb16 = s16.shapes.add_textbox(Inches(2.7), Inches(2.2), Inches(7.9), Inches(3.2))
    tf16 = tb16.text_frame
    tf16.word_wrap = True
    
    p = tf16.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    p.text = "THANK YOU!"
    p.font.size = Pt(40)
    p.font.bold = True
    p.font.color.rgb = EMERALD
    p.space_after = Pt(12)
    
    p2 = tf16.add_paragraph()
    p2.alignment = PP_ALIGN.CENTER
    p2.text = "Vaani AI: AI-Powered Voice-to-Text Analysis and Multilingual Conversational Assistant"
    p2.font.size = Pt(16)
    p2.font.bold = True
    p2.font.color.rgb = TEXT_WHITE
    p2.space_after = Pt(16)
    
    p3 = tf16.add_paragraph()
    p3.alignment = PP_ALIGN.CENTER
    p3.text = "Questions & Demonstration\nLive Server: http://127.0.0.1:5000\nProject Guide: Prof. Sagar Jain"
    p3.font.size = Pt(14)
    p3.font.color.rgb = ACCENT_BLUE

    prs.save(OUTPUT_PPTX)
    print(f"Presentation successfully generated at: {OUTPUT_PPTX}")

if __name__ == "__main__":
    build_presentation()
