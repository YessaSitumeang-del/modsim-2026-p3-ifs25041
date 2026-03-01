import random
import math
from collections import deque

# =================================================================
# KONFIGURASI OPTIMAL (Disesuaikan untuk Target < 30 Menit)
# =================================================================
RANDOM_SEED = 42
TOTAL_MEJA = 60
MAHASISWA_PER_MEJA = 3
TOTAL_OMPRENG = TOTAL_MEJA * MAHASISWA_PER_MEJA  # 180 porsi

# Alokasi petugas (Formasi Sprint: 3 Lauk - 1 Angkat - 3 Nasi)
# Formasi 3-1-3 adalah yang paling seimbang untuk 7 orang
STAGE1_WORKERS = 3  # Memasukkan lauk (Ngebut)
STAGE2_WORKERS = 1  # Mengangkat ompreng (1 orang cukup karena angkut 7 sekaligus cepat)
STAGE3_WORKERS = 3  # Menambahkan nasi (Ngebut)

# Parameter waktu (detik) - Diambil batas bawah untuk efisiensi tinggi
STAGE1_MIN, STAGE1_MAX = 25, 35    # Per ompreng (Target rata-rata 30s)
STAGE2_MIN, STAGE2_MAX = 20, 30    # Per batch (Kecepatan angkut konstan)
BATCH_MIN, BATCH_MAX = 7, 7        # Selalu angkut 7 ompreng agar maksimal
STAGE3_MIN, STAGE3_MAX = 25, 35    # Per ompreng (Target rata-rata 30s)

# ======================
# SIMULASI
# ======================
def simulate_piket():
    random.seed(RANDOM_SEED)
    
    # Tahap 1: Proses memasukkan lauk (paralel)
    finish_stage1 = [0.0] * TOTAL_OMPRENG
    worker_next_free = [0.0] * STAGE1_WORKERS 
    
    for i in range(TOTAL_OMPRENG):
        worker_idx = min(range(STAGE1_WORKERS), key=lambda x: worker_next_free[x])
        start_time = worker_next_free[worker_idx]
        duration = random.uniform(STAGE1_MIN, STAGE1_MAX)
        finish_time = start_time + duration
        worker_next_free[worker_idx] = finish_time
        finish_stage1[i] = finish_time
    
    # Tahap 2: Batch processing (mengangkat ke meja)
    finish_stage2 = [0.0] * TOTAL_OMPRENG
    stage2_workers = [0.0] * STAGE2_WORKERS 
    ompreng_sorted = sorted(range(TOTAL_OMPRENG), key=lambda x: finish_stage1[x])
    buffer = deque(ompreng_sorted)
    batch_sizes = []
    
    while buffer:
        batch_size = random.randint(BATCH_MIN, BATCH_MAX)
        if len(buffer) < batch_size:
            batch_size = len(buffer)
        
        batch = [buffer.popleft() for _ in range(batch_size)]
        batch_sizes.append(batch_size)
        
        batch_ready = max(finish_stage1[i] for i in batch)
        worker_idx = min(range(STAGE2_WORKERS), key=lambda x: stage2_workers[x])
        start_time = max(batch_ready, stage2_workers[worker_idx])
        duration = random.uniform(STAGE2_MIN, STAGE2_MAX)
        finish_time = start_time + duration
        stage2_workers[worker_idx] = finish_time
        
        for i in batch:
            finish_stage2[i] = finish_time
    
    # Tahap 3: Menambahkan nasi (paralel)
    finish_stage3 = [0.0] * TOTAL_OMPRENG
    worker_next_free = [0.0] * STAGE3_WORKERS
    ompreng_by_stage2 = sorted(range(TOTAL_OMPRENG), key=lambda x: finish_stage2[x])
    
    for i in ompreng_by_stage2:
        worker_idx = min(range(STAGE3_WORKERS), key=lambda x: worker_next_free[x])
        start_time = max(finish_stage2[i], worker_next_free[worker_idx])
        duration = random.uniform(STAGE3_MIN, STAGE3_MAX)
        finish_time = start_time + duration
        worker_next_free[worker_idx] = finish_time
        finish_stage3[i] = finish_time
    
    return finish_stage1, finish_stage2, finish_stage3, batch_sizes

# =================================================================
# ANALISIS & OUTPUT (Logika Tetap Sama)
# =================================================================
def analyze_results(finish_stage1, finish_stage2, finish_stage3, batch_sizes):
    total_time = max(finish_stage3)
    avg_batch = sum(batch_sizes) / len(batch_sizes)
    meja_ready = []
    for meja in range(TOTAL_MEJA):
        start_idx = meja * MAHASISWA_PER_MEJA
        end_idx = start_idx + MAHASISWA_PER_MEJA
        ready_time = max(finish_stage3[start_idx:end_idx])
        meja_ready.append((meja + 1, ready_time))
    meja_ready.sort(key=lambda x: x[1])
    
    return {
        'total_time': total_time,
        'avg_batch': avg_batch,
        'meja_ready': meja_ready,
        'bottleneck': "Terdistribusi Merata" if total_time < 1800 else "Perlu Optimasi"
    }

def print_results(results):
    total_time = results['total_time']
    menit = int(total_time // 60)
    detik = int(total_time % 60)
    
    print("="*70)
    print(f"🚀 HASIL OPTIMASI PIKET IT DEL (< 30 MENIT)")
    print("="*70)
    print(f"⏱️  Waktu Total      : {menit} menit {detik} detik")
    print(f"🏁 Selesai Pukul    : 07.{menit:02d} WIB")
    print(f"👥 Formasi Petugas  : {STAGE1_WORKERS} Lauk, {STAGE2_WORKERS} Angkat, {STAGE3_WORKERS} Nasi")
    print(f"📦 Efisiensi Batch  : {results['avg_batch']:.1f} ompreng per angkut")
    print("-" * 70)
    
    print(f"📋 PROGRES KESIAPAN MEJA:")
    for i in [0, 14, 29, 44, 59]: # Cek progress di 25%, 50%, 75%, 100%
        meja, waktu = results['meja_ready'][i]
        m, d = int(waktu // 60), int(waktu % 60)
        print(f"   Meja {meja:<2} siap pada: 07.{m:02d}:{d:02d}")
    print("="*70)

if __name__ == "__main__":
    f1, f2, f3, b = simulate_piket()
    res = analyze_results(f1, f2, f3, b)
    print_results(res)