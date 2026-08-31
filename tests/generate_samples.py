import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

SAMPLE_DIR = Path(__file__).resolve().parent.parent / "sample_pdfs"
SAMPLE_DIR.mkdir(parents=True, exist_ok=True)

def create_pdf(filename: str, title: str, author: str, paragraphs: list):
    filepath = SAMPLE_DIR / filename
    doc = SimpleDocTemplate(
        str(filepath),
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=colors.HexColor('#0f172a'),
        spaceAfter=6
    )
    author_style = ParagraphStyle(
        'DocAuthor',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#475569'),
        spaceAfter=14
    )
    heading_style = ParagraphStyle(
        'DocSection',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#1e293b'),
        spaceBefore=10,
        spaceAfter=4
    )
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor('#334155'),
        spaceAfter=8
    )

    story = [
        Paragraph(title, title_style),
        Paragraph(f"<b>Author:</b> {author} | <i>Department of Computer Science & Engineering</i>", author_style),
        Spacer(1, 8)
    ]

    for item in paragraphs:
        if item.get('type') == 'heading':
            story.append(Paragraph(item['text'], heading_style))
        else:
            story.append(Paragraph(item['text'], body_style))

    doc.build(story)
    print(f"Generated sample PDF: {filepath}")

def generate_all_samples():
    # 1. Invalid Format (Short word count ~110 words, missing Methodology & Results)
    create_pdf(
        filename="01_invalid_format.pdf",
        title="Predictive AI in Modern Web Platforms",
        author="Alex Rivera",
        paragraphs=[
            {"type": "heading", "text": "1. Introduction"},
            {"type": "body", "text": "Artificial intelligence is becoming increasingly important for web applications and digital service platforms. Modern websites process massive volumes of clickstream traffic every single second. By predicting user intent, web servers can dynamically optimize page loading speed, pre-fetch recommended products, and personalize navigation interfaces."},
            {"type": "heading", "text": "2. Conclusion"},
            {"type": "body", "text": "In conclusion, applying AI models to web platforms provides significant user experience improvements. Future work will explore integrating real-time prediction algorithms onto edge content delivery networks."}
        ]
    )

    # 2. Copied Idea (Compliant structure & ~320 words, but standard generic MNIST CNN tutorial)
    create_pdf(
        filename="02_copied_idea.pdf",
        title="Handwritten Digit Recognition using Convolutional Neural Networks on MNIST",
        author="David Chen",
        paragraphs=[
            {"type": "heading", "text": "1. Introduction"},
            {"type": "body", "text": "Optical character recognition and automated document processing remain foundational challenges in computer vision and machine learning applications across industry and academia. Accurately classifying handwritten numeric digits is essential for automated postal mail sorting, commercial bank cheque processing, tax document ingestion, and digital archival workflows. This proposal implements a standard supervised deep learning classifier to recognize isolated grayscale digits ranging from zero to nine with high throughput."},
            {"type": "heading", "text": "2. Methodology"},
            {"type": "body", "text": "We evaluate a sequential Convolutional Neural Network architecture built using standard 3x3 convolutional filters, batch normalization layers, ReLU activation functions, and max-pooling layers for spatial subsampling. The model is trained on the canonical MNIST benchmark dataset comprising 60,000 training images and 10,000 testing images of dimension 28x28 pixels with centered numerals. Optimization is conducted using categorical cross-entropy loss and the standard Adam optimizer initialized with default learning parameters. Dropout regularization (rate 0.25) is applied before the final softmax dense classification layer to prevent parameter overfitting."},
            {"type": "heading", "text": "3. Results"},
            {"type": "body", "text": "The convolutional model converges within fifteen training epochs, achieving a test accuracy of 98.7% on the MNIST evaluation partition. Confusion matrix diagnostics indicate that residual classification errors predominantly occur between visually ambiguous numeral pairs such as digits four and nine, or three and five."},
            {"type": "heading", "text": "4. Conclusion"},
            {"type": "body", "text": "The study demonstrates that standard convolutional networks reliably achieve high accuracy on benchmark digit recognition datasets. However, because the MNIST benchmark is widely considered saturated and well-established in standard classroom tutorials, future investigations should evaluate transferability across complex real-world alphanumeric datasets."}
        ]
    )

    # 3. Innovative Idea (Compliant structure, ~360 words, novel edge computing algorithm)
    create_pdf(
        filename="03_innovative_idea.pdf",
        title="Neuromorphic Hyperdimensional Computing on Edge MEMS for Sub-Microwatt Cardiac Anomaly Detection",
        author="Dr. Priya Nair & Marcus Vance",
        paragraphs=[
            {"type": "heading", "text": "1. Introduction"},
            {"type": "body", "text": "Continuous wearable cardiac telemetry requires real-time electrocardiogram (ECG) arrhythmia classification on ultra-low-power biomedical edge devices. Conventional deep neural networks incur prohibitive memory footprints and memory bandwidth bottlenecks, exceeding the micro-watt energy budgets of miniaturized implantable sensors. This research introduces a spike-driven Hyperdimensional Computing (HDC) architecture that maps continuous multi-channel physiological signals into pseudo-orthogonal 8,192-bit holographic vector representations."},
            {"type": "heading", "text": "2. Methodology"},
            {"type": "body", "text": "Our proposed framework couples an asynchronous event-based delta modulator with a hardware-friendly ternary hyperdimensional encoder. Raw voltage samples from the MIT-BIH Arrhythmia Database are converted into sparse temporal spike trains. A randomized continuous item memory projects QRS complex intervals into high-dimensional hyperspace using non-linear circular convolution and permutation operators. Single-pass online associative learning is performed directly on-chip using localized hardware XNOR-popcount primitives, eliminating off-chip gradient backpropagation overheads entirely."},
            {"type": "heading", "text": "3. Results"},
            {"type": "body", "text": "Evaluated against 48 patient records from PhysioNet MIT-BIH benchmarks, the neuromorphic HDC pipeline achieves a 97.4% ventricular ectopic beat classification accuracy and 98.1% F1-score. Synthesized in a 22nm FD-SOI semiconductor process, the full inference core consumes only 840 nanowatts at 0.5V supply voltage, delivering a 24x energy efficiency advantage compared to quantized edge CNN baselines."},
            {"type": "heading", "text": "4. Conclusion"},
            {"type": "body", "text": "This work validates spike-driven hyperdimensional vector representations as an ultra-low-power computing paradigm for continuous biomedical diagnostics. Future iterations will fabricate monolithic silicon prototypes with integrated piezoelectric energy harvesting."}
        ]
    )

if __name__ == "__main__":
    generate_all_samples()
