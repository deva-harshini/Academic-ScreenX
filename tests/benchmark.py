import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import time
from typing import List, Dict, Any
from app.agents.pipeline import pipeline_engine

TEST_ABSTRACTS = [
    {
        "title": "Neuromorphic Hyperdimensional Computing on Edge MEMS for Sub-Milliwatt Anomaly Detection",
        "text": """1. Introduction
Modern edge computing environments face severe power and memory constraints when deploying deep neural networks for continuous sensory monitoring. Traditional edge microcontrollers running quantized convolutional architectures still consume tens of milliwatts, making battery-less deployment unfeasible for distributed Internet-of-Things (IoT) sensor nodes.

2. Methodology
We introduce a hybrid hardware-software architecture coupling sub-threshold Micro-Electro-Mechanical Systems (MEMS) acoustic transducers directly with an ultra-low-power hyperdimensional computing (HDC) accelerator. The continuous sensory stream from resonant MEMS sensors is digitized via asynchronous level-crossing analog-to-digital converters and projected into high-dimensional binary hyperspace (D = 8,192). We implement an on-chip associative memory engine that performs non-linear similarity evaluation and online single-pass learning using localized bit-level vector operations. Furthermore, the architecture eliminates floating-point matrix multiplications entirely, replacing them with circular bit-shifts and XOR accumulators to minimize dynamic switching activity across the silicon substrate.

3. Results & Evaluation
Experimental validation on the industrial bearing vibration benchmark demonstrates that our neuromorphic HDC architecture achieves a 96.4% F1-score in detecting anomalous mechanical degradation. The entire system operates with a total power consumption of 412 microwatts, delivering an 18x reduction in energy per inference compared to optimized ARM Cortex-M4 baselines while operating within strict 15-millisecond latency bounds.

4. Conclusion & Impact
The proposed edge MEMS hyperdimensional system proves that zero-latency anomaly detection is feasible within sub-milliwatt power envelopes, enabling self-powered persistent sensing across smart manufacturing nodes and industrial IoT deployments with minimal maintenance overhead."""
    },
    {
        "title": "Handwritten Digit Recognition using Convolutional Neural Networks on MNIST",
        "text": """1. Introduction
Handwritten character recognition is an essential component of document digitalization and automated postal sorting pipelines. Accurately classifying handwritten digits poses significant variability in stroke thickness, orientation, and writing styles across different writers, requiring automated image filtering.

2. Methodology
In this project, we implement a classic LeNet-inspired Convolutional Neural Network (CNN) architecture using PyTorch. The model consists of two 2D convolutional layers with 5x5 kernels, rectified linear unit (ReLU) activation functions, 2x2 max pooling layers, and two fully connected dense layers. Training is conducted on the standard MNIST dataset consisting of 60,000 training and 10,000 test grayscale images of size 28x28 pixels using the Adam optimizer with cross-entropy loss over 20 epochs. The network architecture strictly follows standard deep learning textbook implementations without additional architectural regularization or novelty.

3. Experimental Results
The trained CNN baseline achieves an accuracy of 98.2% on the test split. We evaluate the training loss curves and plot the confusion matrix to analyze misclassified digits. The empirical results demonstrate that convolutional feature extraction is effective for standard digit recognition tasks on benchmark images.

4. Conclusion
We successfully replicate the standard convolutional network pipeline for digit recognition on the MNIST benchmark dataset. Future work could examine data augmentation techniques."""
    },
    {
        "title": "Predictive AI in Web Platforms",
        "text": """1. Introduction: Modern web platforms require fast data scraping.
2. Methodology: We build a fast web scraper.
4. Conclusion: The system functions as expected."""
    }
]

def run_performance_benchmark(iterations: int = 10):
    print("STARTING ACADEMIC-SCREENX PIPELINE BENCHMARK")
    print(f"Executing {iterations} rounds across {len(TEST_ABSTRACTS)} test profiles...")
    print("=" * 60)

    latencies: List[float] = []
    triage_counts: Dict[str, int] = {"Approved": 0, "Needs Revision": 0, "Flagged": 0}

    start_total_time = time.perf_counter()

    for i in range(iterations):
        for sample in TEST_ABSTRACTS:
            t0 = time.perf_counter()
            
            result = pipeline_engine.run_pipeline(
                title=sample["title"],
                extracted_text=sample["text"]
            )
            
            t1 = time.perf_counter()
            elapsed = t1 - t0
            latencies.append(elapsed)

            status = getattr(result, "triage_status", "") if hasattr(result, "triage_status") else (result.get("triage_status", "") if isinstance(result, dict) else "")
            
            if "Approved" in status:
                triage_counts["Approved"] += 1
            elif "Revision" in status:
                triage_counts["Needs Revision"] += 1
            else:
                triage_counts["Flagged"] += 1

    end_total_time = time.perf_counter()
    total_time = end_total_time - start_total_time
    total_processed = len(latencies)

    avg_latency = sum(latencies) / total_processed
    min_latency = min(latencies)
    max_latency = max(latencies)
    throughput = total_processed / total_time

    print("\n" + "=" * 60)
    print("BENCHMARK EVALUATION RESULTS")
    print("=" * 60)
    print(f"Total Abstracts Processed  : {total_processed}")
    print(f"Total Execution Time       : {total_time:.3f} seconds")
    print(f"Average Processing Latency : {avg_latency * 1000:.2f} ms per abstract")
    print(f"Min / Max Latency          : {min_latency * 1000:.2f} ms / {max_latency * 1000:.2f} ms")
    print(f"System Throughput          : {throughput:.2f} abstracts/sec")
    print("TRIAGE DISTRIBUTION BREAKDOWN:")
    for status_name, count in triage_counts.items():
        percentage = (count / total_processed) * 100
        print(f"  - {status_name:<16}: {count} ({percentage:.1f}%)")
    print("\n")

if __name__ == "__main__":
    run_performance_benchmark(iterations=10)
