import tensorflow as tf
import time

print("TensorFlow Version:", tf.__version__)
print("Available GPUs:", tf.config.list_physical_devices('GPU'))

size = 10000
A = tf.random.normal((size, size))
B = tf.random.normal((size, size))

def benchmark_device(device):
    with tf.device(device):
        start_time = time.time()
        result = tf.matmul(A, B)
        _ = result.numpy()
        end_time = time.time()
    return end_time - start_time

cpu_time = benchmark_device('/CPU:0')
print(f"CPU Time: {cpu_time:.4f} seconds")

gpu_devices = tf.config.list_physical_devices('GPU')
if gpu_devices:
    gpu_time = benchmark_device('/GPU:0')
    print(f"GPU Time: {gpu_time:.4f} seconds")
else:
    print("No GPU available.")
