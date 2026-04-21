import time
import numpy as np

def test_detector_throughput(detector):
    data = np.random.normal(0.5, 0.1, (1000, 32))
    start = time.time()
    detector.predict(data)
    duration = time.time() - start
    throughput = 1000 / duration
    print(f"\nThroughput Detector: {throughput:.2f} events/sec")
    assert throughput > 1000

def test_monitor_throughput(monitor):
    start = time.time()
    for _ in range(100):
        monitor.capture_metrics()
    duration = time.time() - start
    throughput = 100 / duration
    print(f"\nThroughput Monitor: {throughput:.2f} events/sec")
    assert throughput > 10
