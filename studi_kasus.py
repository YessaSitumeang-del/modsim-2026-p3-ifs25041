import random
import math
from collections import deque

# ======================
# KONFIGURASI
# ======================
RANDOM_SEED = 42
TOTAL_MEJA = 60
MAHASISWA_PER_MEJA = 3
TOTAL_OMPRENG = TOTAL_MEJA * MAHASISWA_PER_MEJA  # 180 porsi

# Alokasi petugas
STAGE1_WORKERS = 3  # Memasukkan lauk
STAGE2_WORKERS = 2  # Mengangkat ompreng (batch)
STAGE3_WORKERS = 2  # Menambahkan nasi

# Parameter waktu (detik)
STAGE1_MIN, STAGE1_MAX = 30, 60    # Per ompreng
STAGE2_MIN, STAGE2_MAX = 20, 60    # Per batch
BATCH_MIN, BATCH_MAX = 4, 7        # Ompreng per batch
STAGE3_MIN, STAGE3_MAX = 30, 60    # Per ompreng

# ======================
# SIMULASI
# ======================
def simulate_piket():
    random.seed(RANDOM_SEED)
    
    # Tahap 1: Proses memasukkan lauk (paralel)
    finish_stage1 = [0.0] * TOTAL_OMPRENG
    worker_next_free = [0.0] * STAGE1_WORKERS  # Waktu kapan worker available
    
    for i in range(TOTAL_OMPRENG):
        # Pilih worker yang paling cepat available
        worker_idx = min(range(STAGE1_WORKERS), key=lambda x: worker_next_free[x])
        start_time = worker_next_free[worker_idx]
        duration = random.uniform(STAGE1_MIN, STAGE1_MAX)
        finish_time = start_time + duration
        worker_next_free[worker_idx] = finish_time
        finish_stage1[i] = finish_time
    
    # Tahap 2: Batch processing (mengangkat ke meja)
    finish_stage2 = [0.0] * TOTAL_OMPRENG
    stage2_workers = [0.0] * STAGE2_WORKERS  # Waktu available worker tahap 2
    ompreng_sorted = sorted(range(TOTAL_OMPRENG), key=lambda x: finish_stage1[x])
    buffer = deque(ompreng_sorted)
    batch_sizes = []
    
    while buffer:
        # Tentukan ukuran batch
        batch_size = random.randint(BATCH_MIN, BATCH_MAX)
        if len(buffer) < batch_size:
            batch_size = len(buffer)
        
        batch = [buffer.popleft() for _ in range(batch_size)]
        batch_sizes.append(batch_size)
        
        # Waktu batch siap = waktu selesai ompreng terakhir dalam batch
        batch_ready = max(finish_stage1[i] for i in batch)
        
        # Pilih worker tahap 2 yang paling cepat available
        worker_idx = min(range(STAGE2_WORKERS), key=lambda x: stage2_workers[x])
        start_time = max(batch_ready, stage2_workers[worker_idx])
        duration = random.uniform(STAGE2_MIN, STAGE2_MAX)
        finish_time = start_time + duration
        stage2_workers[worker_idx] = finish_time
        
        # Set waktu selesai semua ompreng dalam batch
        for i in batch:
            finish_stage2[i] = finish_time
    
    # Tahap 3: Menambahkan nasi (paralel)
    finish_stage3 = [0.0] * TOTAL_OMPRENG
    worker_next_free = [0.0] * STAGE3_WORKERS
    
    # Urutkan ompreng berdasarkan waktu selesai tahap 2
    ompreng_by_stage2 = sorted(range(TOTAL_OMPRENG), key=lambda x: finish_stage2[x])
    
    for i in ompreng_by_stage2:
        worker_idx = min(range(STAGE3_WORKERS), key=lambda x: worker_next_free[x])
        start_time = max(finish_stage2[i], worker_next_free[worker_idx])
        duration = random.uniform(STAGE3_MIN, STAGE3_MAX)
        finish_time = start_time + duration
        worker_next_free[worker_idx] = finish_time
        finish_stage3[i] = finish_time
    
    return finish_stage1, finish_stage2, finish_stage3, batch_sizes

# ======================
# ANALISIS HASIL
# ======================
def analyze_results(finish_stage1, finish_stage2, finish_stage3, batch_sizes):
    total_time = max(finish_stage3)
    avg_batch = sum(batch_sizes) / len(batch_sizes)
    
    # Hitung waktu kesiapan per meja (meja siap jika 3 omprengnya selesai)
    meja_ready = []
    for meja in range(TOTAL_MEJA):
        start_idx = meja * MAHASISWA_PER_MEJA
        end_idx = start_idx + MAHASISWA_PER_MEJA
        ready_time = max(finish_stage3[start_idx:end_idx])
        meja_ready.append((meja + 1, ready_time))
    
    meja_ready.sort(key=lambda x: x[1])
    
    # Analisis bottleneck (berdasarkan utilization)
    stage1_total_work = sum([random.uniform(STAGE1_MIN, STAGE1_MAX) for _ in range(TOTAL_OMPRENG)])
    stage1_capacity = STAGE1_WORKERS * total_time
    stage1_util = min(100, (stage1_total_work / stage1_capacity) * 100)
    
    stage2_total_work = sum([random.uniform(STAGE2_MIN, STAGE2_MAX) for _ in batch_sizes])
    stage2_capacity = STAGE2_WORKERS * total_time
    stage2_util = min(100, (stage2_total_work / stage2_capacity) * 100)
    
    stage3_total_work = sum([random.uniform(STAGE3_MIN, STAGE3_MAX) for _ in range(TOTAL_OMPRENG)])
    stage3_capacity = STAGE3_WORKERS * total_time
    stage3_util = min(100, (stage3_total_work / stage3_capacity) * 100)
    
    bottleneck = max([
        ("Tahap 1 (Lauk)", stage1_util),
        ("Tahap 2 (Angkat)", stage2_util),
        ("Tahap 3 (Nasi)", stage3_util)
    ], key=lambda x: x[1])[0]
    
    return {
        'total_time': total_time,
        'avg_batch': avg_batch,
        'meja_ready': meja_ready,
        'stage1_util': stage1_util,
        'stage2_util': stage2_util,
        'stage3_util': stage3_util,
        'bottleneck': bottleneck
    }

# ======================
# OUTPUT TERMINAL
# ======================
def print_results(results):
    total_time = results['total_time']
    menit = int(total_time // 60)
    detik = int(total_time % 60)
    selesai_jam = 7 + menit // 60
    selesai_menit = menit % 60
    
    print("="*70)
    print(" SIMULASI SISTEM PIKET MAKAN SIANG IT DEL - OUTPUT TERMINAL")
    print("="*70)
    print(f"\n📊 KONFIGURASI:")
    print(f"   Total meja          : {TOTAL_MEJA}")
    print(f"   Mahasiswa per meja  : {MAHASISWA_PER_MEJA}")
    print(f"   Total ompreng       : {TOTAL_OMPRENG}")
    print(f"   Alokasi petugas     : Tahap1={STAGE1_WORKERS}, Tahap2={STAGE2_WORKERS}, Tahap3={STAGE3_WORKERS}")
    print(f"   Waktu mulai         : 07.00 WIB")
    
    print(f"\n⏱️  HASIL SIMULASI:")
    print(f"   Waktu total         : {menit} menit {detik} detik ({total_time:.1f} detik)")
    print(f"   Perkiraan selesai   : {selesai_jam:02d}.{selesai_menit:02d} WIB")
    print(f"   Rata-rata batch     : {results['avg_batch']:.2f} ompreng/batch")
    
    print(f"\n📈 UTILISASI PETUGAS:")
    print(f"   Tahap 1 (Lauk)      : {results['stage1_util']:.1f}%")
    print(f"   Tahap 2 (Angkat)    : {results['stage2_util']:.1f}%")
    print(f"   Tahap 3 (Nasi)      : {results['stage3_util']:.1f}%")
    print(f"\n⚠️  BOTTLENECK         : {results['bottleneck']}")
    
    print(f"\n📋 KESIAPAN MEJA (Contoh 10 meja pertama & terakhir):")
    print(f"   {'Meja':<6} {'Waktu Siap':<15} {'Pukul'}")
    print(f"   {'-'*40}")
    
    # 5 meja pertama
    for i in range(5):
        meja, waktu = results['meja_ready'][i]
        m = int(waktu // 60)
        d = int(waktu % 60)
        print(f"   {meja:<6} {m} menit {d:02d} detik   07.{(7 + m) % 60:02d}")
    
    print(f"   ...")
    
    # 5 meja terakhir
    for i in range(-5, 0):
        meja, waktu = results['meja_ready'][i]
        m = int(waktu // 60)
        d = int(waktu % 60)
        jam = 7 + m // 60
        menit = m % 60
        print(f"   {meja:<6} {m} menit {d:02d} detik   {jam:02d}.{menit:02d}")
    
    print(f"\n💡 REKOMENDASI OPTIMASI:")
    if "Tahap 3" in results['bottleneck']:
        print(f"   • Tambah 1 petugas di Tahap 3 (nasi) → alokasi 3-2-2")
        print(f"   • Targetkan batch 6 ompreng di Tahap 2 untuk efisiensi")
    elif "Tahap 1" in results['bottleneck']:
        print(f"   • Tambah 1 petugas di Tahap 1 (lauk) → alokasi 2-2-3")
    else:
        print(f"   • Sistem sudah seimbang. Pertahankan alokasi saat ini.")
    
    print(f"\n" + "="*70)
    print(f" Simulasi selesai. Estimasi waktu: {menit}–{menit+5} menit (08.{selesai_menit:02d}–08.{selesai_menit+5:02d} WIB)")
    print("="*70)

# ======================
# EKSEKUSI
# ======================
if __name__ == "__main__":
    print("Memulai simulasi sistem piket IT Del...")
    print("Mohon tunggu sebentar (simulasi berjalan dalam < 1 detik)...\n")
    
    # Jalankan simulasi
    finish1, finish2, finish3, batches = simulate_piket()
    
    # Analisis hasil
    results = analyze_results(finish1, finish2, finish3, batches)
    
    # Tampilkan output
    print_results(results)