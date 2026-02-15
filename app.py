import streamlit as st
import random
from collections import deque
import plotly.graph_objects as go
import pandas as pd

# ======================
# PAGE CONFIGURATION
# ======================
st.set_page_config(
    page_title="Simulasi Prasmanan di Kantin ITDel",
    page_icon="🍚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ======================
# STYLING
# ======================
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #43A047;
        margin-top: 2rem;
    }
    .sidebar-section {
        background-color: #2d2d2d;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    .sidebar-title {
        font-weight: bold;
        color: #f0f0f0;
        margin-bottom: 0.5rem;
    }
    .instruction-box {
        background-color: #1a2b4d;
        border-radius: 0.5rem;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
    }
    .step {
        margin-bottom: 0.5rem;
        padding-left: 1.5rem;
    }
    .step-number {
        font-weight: bold;
        color: #4fc3f7;
        margin-right: 0.5rem;
    }
    .parameter-label {
        color: #f0f0f0;
        font-weight: 500;
        margin-bottom: 0.25rem;
    }
    .parameter-value {
        color: #e0e0e0;
        font-size: 0.9rem;
        margin-bottom: 0.5rem;
    }
    .bottleneck-warning {
        background-color: #5d2626;
        border-left: 5px solid #d32f2f;
        padding: 1rem;
        border-radius: 0 0.5rem 0.5rem 0;
        margin: 1rem 0;
    }
    .bottleneck-suggestion {
        background-color: #2d3748;
        border-left: 5px solid #4299e1;
        padding: 1rem;
        border-radius: 0 0.5rem 0.5rem 0;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #2c5282;
        border-left: 5px solid #3182ce;
        padding: 1rem;
        border-radius: 0 0.5rem 0.5rem 0;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# ======================
# SIMULATION FUNCTIONS
# ======================
def simulate_piket(config):
    """Simulasi sistem piket dengan konfigurasi tertentu"""
    random.seed(config['random_seed'])
    
    TOTAL_OMPRENG = config['total_meja'] * config['mahasiswa_per_meja']
    
    # Tahap 1: Proses memasukkan lauk (paralel)
    finish_stage1 = [0.0] * TOTAL_OMPRENG
    worker_next_free = [0.0] * config['stage1_workers']
    
    for i in range(TOTAL_OMPRENG):
        worker_idx = min(range(config['stage1_workers']), key=lambda x: worker_next_free[x])
        start_time = worker_next_free[worker_idx]
        duration = random.uniform(config['stage1_min'], config['stage1_max'])
        finish_time = start_time + duration
        worker_next_free[worker_idx] = finish_time
        finish_stage1[i] = finish_time
    
    # Tahap 2: Batch processing (mengangkat ke meja)
    finish_stage2 = [0.0] * TOTAL_OMPRENG
    stage2_workers = [0.0] * config['stage2_workers']
    ompreng_sorted = sorted(range(TOTAL_OMPRENG), key=lambda x: finish_stage1[x])
    buffer = deque(ompreng_sorted)
    batch_sizes = []
    
    while buffer:
        batch_size = random.randint(config['batch_min'], config['batch_max'])
        if len(buffer) < batch_size:
            batch_size = len(buffer)
        
        batch = [buffer.popleft() for _ in range(batch_size)]
        batch_sizes.append(batch_size)
        
        batch_ready = max(finish_stage1[i] for i in batch)
        
        worker_idx = min(range(config['stage2_workers']), key=lambda x: stage2_workers[x])
        start_time = max(batch_ready, stage2_workers[worker_idx])
        duration = random.uniform(config['stage2_min'], config['stage2_max'])
        finish_time = start_time + duration
        stage2_workers[worker_idx] = finish_time
        
        for i in batch:
            finish_stage2[i] = finish_time
    
    # Tahap 3: Menambahkan nasi (paralel)
    finish_stage3 = [0.0] * TOTAL_OMPRENG
    worker_next_free = [0.0] * config['stage3_workers']
    
    ompreng_by_stage2 = sorted(range(TOTAL_OMPRENG), key=lambda x: finish_stage2[x])
    
    for i in ompreng_by_stage2:
        worker_idx = min(range(config['stage3_workers']), key=lambda x: worker_next_free[x])
        start_time = max(finish_stage2[i], worker_next_free[worker_idx])
        duration = random.uniform(config['stage3_min'], config['stage3_max'])
        finish_time = start_time + duration
        worker_next_free[worker_idx] = finish_time
        finish_stage3[i] = finish_time
    
    return finish_stage1, finish_stage2, finish_stage3, batch_sizes

def analyze_results(config, finish_stage1, finish_stage2, finish_stage3, batch_sizes):
    """Analisis hasil simulasi"""
    TOTAL_OMPRENG = config['total_meja'] * config['mahasiswa_per_meja']
    
    total_time = max(finish_stage3)
    avg_batch = sum(batch_sizes) / len(batch_sizes)
    
    # Waktu kesiapan per meja
    meja_ready = []
    for meja in range(config['total_meja']):
        start_idx = meja * config['mahasiswa_per_meja']
        end_idx = start_idx + config['mahasiswa_per_meja']
        ready_time = max(finish_stage3[start_idx:end_idx])
        meja_ready.append({
            'meja': meja + 1,
            'waktu': ready_time,
            'menit': int(ready_time // 60),
            'detik': int(ready_time % 60),
            'jam': 7 + int(ready_time // 3600),
            'menit_jam': int((ready_time % 3600) // 60)
        })
    
    meja_ready.sort(key=lambda x: x['waktu'])
    
    # Utilisasi petugas
    stage1_total_work = sum([random.uniform(config['stage1_min'], config['stage1_max']) for _ in range(TOTAL_OMPRENG)])
    stage1_capacity = config['stage1_workers'] * total_time
    stage1_util = min(100, (stage1_total_work / stage1_capacity) * 100)
    
    stage2_total_work = sum([random.uniform(config['stage2_min'], config['stage2_max']) for _ in batch_sizes])
    stage2_capacity = config['stage2_workers'] * total_time
    stage2_util = min(100, (stage2_total_work / stage2_capacity) * 100)
    
    stage3_total_work = sum([random.uniform(config['stage3_min'], config['stage3_max']) for _ in range(TOTAL_OMPRENG)])
    stage3_capacity = config['stage3_workers'] * total_time
    stage3_util = min(100, (stage3_total_work / stage3_capacity) * 100)
    
    bottleneck = max([
        ("Tahap 1 (Lauk)", stage1_util),
        ("Tahap 2 (Angkat)", stage2_util),
        ("Tahap 3 (Nasi)", stage3_util)
    ], key=lambda x: x[1])
    
    # DataFrame untuk visualisasi
    df_timeline = pd.DataFrame({
        'ompreng_id': range(TOTAL_OMPRENG),
        'finish_stage1': finish_stage1,
        'finish_stage2': finish_stage2,
        'finish_stage3': finish_stage3
    })
    
    df_meja = pd.DataFrame(meja_ready)
    
    df_utilization = pd.DataFrame({
        'Tahap': ['Tahap 1 (Lauk)', 'Tahap 2 (Angkat)', 'Tahap 3 (Nasi)'],
        'Utilisasi': [stage1_util, stage2_util, stage3_util]
    })
    
    return {
        'total_time': total_time,
        'avg_batch': avg_batch,
        'meja_ready': meja_ready,
        'stage1_util': stage1_util,
        'stage2_util': stage2_util,
        'stage3_util': stage3_util,
        'bottleneck': bottleneck[0],
        'bottleneck_util': bottleneck[1],
        'df_timeline': df_timeline,
        'df_meja': df_meja,
        'df_utilization': df_utilization,
        'batch_sizes': batch_sizes
    }

# ======================
# PLOTLY VISUALIZATIONS
# ======================
def plot_utilization_chart(df_util):
    """Chart utilisasi per tahap"""
    fig = go.Figure()
    
    colors = ['#2196F3', '#4CAF50', '#FF9800']
    
    fig.add_trace(go.Bar(
        x=df_util['Tahap'],
        y=df_util['Utilisasi'],
        marker_color=colors,
        text=[f'{x:.1f}%' for x in df_util['Utilisasi']],
        textposition='auto',
    ))
    
    fig.update_layout(
        title='Utilisasi Petugas Piket per Tahap',
        xaxis_title='Tahap Proses',
        yaxis_title='Utilisasi (%)',
        yaxis=dict(range=[0, 100]),
        height=400,
        template='plotly_white'
    )
    
    return fig

def plot_meja_timeline(df_meja):
    """Timeline kesiapan meja"""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df_meja['meja'],
        y=df_meja['waktu'] / 60,
        mode='lines+markers',
        name='Waktu Kesiapan',
        line=dict(color='#43A047', width=2),
        marker=dict(size=6)
    ))
    
    fig.add_hline(
        y=df_meja['waktu'].max() / 60,
        line_dash="dash",
        line_color="red",
        annotation_text=f"Selesai: {df_meja['waktu'].max() / 60:.1f} menit",
        annotation_position="top right"
    )
    
    fig.update_layout(
        title='Timeline Kesiapan Meja',
        xaxis_title='Nomor Meja',
        yaxis_title='Waktu (menit)',
        height=400,
        template='plotly_white',
        hovermode='x unified'
    )
    
    return fig

def plot_batch_distribution(batch_sizes):
    """Distribusi ukuran batch"""
    fig = go.Figure()
    
    counts = {}
    for size in range(4, 8):
        counts[size] = batch_sizes.count(size)
    
    fig.add_trace(go.Bar(
        x=list(counts.keys()),
        y=list(counts.values()),
        marker_color='#9C27B0',
        text=list(counts.values()),
        textposition='auto',
    ))
    
    avg_batch = sum(batch_sizes) / len(batch_sizes)
    fig.add_vline(
        x=avg_batch,
        line_dash="dash",
        line_color="red",
        annotation_text=f"Rata-rata: {avg_batch:.2f}",
        annotation_position="top"
    )
    
    fig.update_layout(
        title='Distribusi Ukuran Batch Tahap 2',
        xaxis_title='Ukuran Batch (Ompreng)',
        yaxis_title='Frekuensi',
        height=400,
        template='plotly_white'
    )
    
    return fig

def plot_gantt_chart(df_timeline, sample_size=50):
    """Gantt chart untuk sampel ompreng"""
    sample_df = df_timeline.head(sample_size)
    
    fig = go.Figure()
    
    colors = {'Stage 1': '#2196F3', 'Stage 2': '#4CAF50', 'Stage 3': '#FF9800'}
    
    for idx, row in sample_df.iterrows():
        # Stage 1
        fig.add_trace(go.Bar(
            name=f'Ompreng {idx}' if idx == 0 else None,
            x=[row['finish_stage1']],
            y=[f'Ompreng {idx}'],
            orientation='h',
            marker_color=colors['Stage 1'],
            showlegend=False,
            base=0,
            hoverinfo='text',
            hovertext=f'Ompreng {idx}<br>Stage 1: {row["finish_stage1"]:.1f}s'
        ))
        
        # Stage 2
        fig.add_trace(go.Bar(
            x=[row['finish_stage2'] - row['finish_stage1']],
            y=[f'Ompreng {idx}'],
            orientation='h',
            marker_color=colors['Stage 2'],
            showlegend=False,
            base=row['finish_stage1'],
            hoverinfo='text',
            hovertext=f'Ompreng {idx}<br>Stage 2: {row["finish_stage2"]-row["finish_stage1"]:.1f}s'
        ))
        
        # Stage 3
        fig.add_trace(go.Bar(
            x=[row['finish_stage3'] - row['finish_stage2']],
            y=[f'Ompreng {idx}'],
            orientation='h',
            marker_color=colors['Stage 3'],
            showlegend=False,
            base=row['finish_stage2'],
            hoverinfo='text',
            hovertext=f'Ompreng {idx}<br>Stage 3: {row["finish_stage3"]-row["finish_stage2"]:.1f}s'
        ))
    
    # Legenda manual
    for stage, color in colors.items():
        fig.add_trace(go.Bar(
            x=[0], y=[0],
            name=stage,
            marker_color=color,
            showlegend=True
        ))
    
    fig.update_layout(
        title=f'Gantt Chart - {sample_size} Ompreng Pertama',
        xaxis_title='Waktu (detik)',
        yaxis_title='Ompreng ID',
        barmode='stack',
        height=600,
        template='plotly_white',
        showlegend=True,
        legend_title='Tahap Proses'
    )
    
    return fig

# ======================
# MAIN APP
# ======================
def main():
    st.markdown('<div class="main-header">🍚 Simulasi Prasmanan di Kantin ITDel</div>', unsafe_allow_html=True)
    st.markdown("""
    <p style="text-align: center; color: #f0f0f0; font-size: 1.1rem;">
    Simulasi Discrete Event System (DES) untuk analisis kinerja pelayanan prasmanan dengan variasi jumlah petugas piket dan mahasiswa.
    </p>
    """, unsafe_allow_html=True)
    
    # ======================
    # SIDEBAR
    # ======================
    with st.sidebar:
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-title">⚙️ Parameter Simulasi</div>', unsafe_allow_html=True)
        
        # Parameter Simulasi
        st.markdown('<div class="parameter-label">Jumlah Meja</div>', unsafe_allow_html=True)
        total_meja = st.slider("Jumlah Meja", min_value=10, max_value=100, value=60, step=10)
        
        st.markdown('<div class="parameter-label">Mahasiswa per Meja</div>', unsafe_allow_html=True)
        mahasiswa_per_meja = st.slider("Mahasiswa per Meja", min_value=2, max_value=5, value=3, step=1)
        
        st.markdown('<div class="parameter-label">Alokasi Petugas Piket</div>', unsafe_allow_html=True)
        st.markdown('<div class="parameter-value">Format: Tahap 1, Tahap 2, Tahap 3</div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            stage1_workers = st.slider("Tahap 1", min_value=1, max_value=5, value=3, step=1)
        with col2:
            stage2_workers = st.slider("Tahap 2", min_value=1, max_value=5, value=2, step=1)
        with col3:
            stage3_workers = st.slider("Tahap 3", min_value=1, max_value=5, value=2, step=1)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Parameter Waktu Layanan
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-title">⏱️ Parameter Waktu Layanan</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="parameter-label">Waktu Minimum (detik)</div>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            stage1_min = st.slider("Tahap 1", min_value=20, max_value=90, value=30, step=5)
        with col2:
            stage2_min = st.slider("Tahap 2", min_value=15, max_value=90, value=20, step=5)
        col3, col4 = st.columns(2)
        with col3:
            stage3_min = st.slider("Tahap 3", min_value=20, max_value=90, value=30, step=5)
        with col4:
            batch_min = st.slider("Batch Min", min_value=3, max_value=10, value=4, step=1)
        
        st.markdown('<div class="parameter-label">Waktu Maksimum (detik)</div>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            stage1_max = st.slider("Tahap 1 Max", min_value=30, max_value=120, value=60, step=5)
        with col2:
            stage2_max = st.slider("Tahap 2 Max", min_value=20, max_value=120, value=60, step=5)
        col3, col4 = st.columns(2)
        with col3:
            stage3_max = st.slider("Tahap 3 Max", min_value=30, max_value=120, value=60, step=5)
        with col4:
            batch_max = st.slider("Batch Max", min_value=4, max_value=10, value=7, step=1)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Tombol simulasi
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        if st.button("🚀 Jalankan Simulasi", type="primary", use_container_width=True):
            st.session_state.run_simulation = True
        st.markdown('</div>', unsafe_allow_html=True)
    
    # ======================
    # INSTRUCTION BOX
    # ======================
    st.markdown('<div class="instruction-box">', unsafe_allow_html=True)
    st.markdown('<div style="color: #4fc3f7; font-weight: bold; margin-bottom: 0.5rem;">📋 Penjelasan Alokasi Petugas Piket</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div style="color: #f0f0f0; margin-bottom: 1rem;">
    Sistem piket di IT Del menggunakan <strong>7 orang petugas piket</strong> yang dibagi menjadi <strong>3 kelompok</strong> sesuai tahapan proses:
    </div>
    
    <div style="color: #f0f0f0; margin-left: 1.5rem; margin-bottom: 0.5rem;">
    <strong>• 3 Petugas Piket di Tahap 1 (Memasukkan Lauk)</strong><br>
    <span style="color: #e0e0e0; font-size: 0.9rem;">
    Bertugas memasukkan lauk ke dalam ompreng. Setiap petugas mengerjakan 1 ompreng dalam waktu 30-60 detik.
    </span>
    </div>
    
    <div style="color: #f0f0f0; margin-left: 1.5rem; margin-bottom: 0.5rem;">
    <strong>• 2 Petugas Piket di Tahap 2 (Mengangkat Ompreng)</strong><br>
    <span style="color: #e0e0e0; font-size: 0.9rem;">
    Bertugas mengangkat ompreng ke atas meja dengan sistem batch processing. 
    Setiap petugas membawa 4-7 ompreng sekaligus dalam waktu 20-60 detik.
    </span>
    </div>
    
    <div style="color: #f0f0f0; margin-left: 1.5rem; margin-bottom: 0.5rem;">
    <strong>• 2 Petugas Piket di Tahap 3 (Menambahkan Nasi)</strong><br>
    <span style="color: #e0e0e0; font-size: 0.9rem;">
    Bertugas menambahkan nasi ke dalam ompreng yang sudah berada di atas meja. 
    Setiap petugas mengerjakan 1 ompreng dalam waktu 30-60 detik.
    </span>
    </div>
    
    <div style="margin-top: 1rem; color: #4fc3f7; font-weight: bold;">🚀 Cara Menggunakan Simulasi</div>
    <div class="step"><span class="step-number">1.</span> Atur parameter simulasi di sidebar kiri</div>
    <div class="step"><span class="step-number">2.</span> Klik tombol "Jalankan Simulasi"</div>
    <div class="step"><span class="step-number">3.</span> Tunggu proses simulasi selesai</div>
    <div class="step"><span class="step-number">4.</span> Lihat hasil dan visualisasi</div>
    
    <div style="margin-top: 1rem; color: #e0e0e0;">Parameter default:</div>
    <div style="color: #f0f0f0; margin-left: 1rem;">• Jumlah Meja: 60</div>
    <div style="color: #f0f0f0; margin-left: 1rem;">• Mahasiswa per Meja: 3</div>
    <div style="color: #f0f0f0; margin-left: 1rem;">• Alokasi Petugas: 3, 2, 2</div>
    <div style="color: #f0f0f0; margin-left: 1rem;">• Total Porsi: 180</div>
    <div style="color: #f0f0f0; margin-left: 1rem;">• Jam Mulai: 07:00 WIB</div>
    
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # ======================
    # SIMULATION EXECUTION
    # ======================
    if st.session_state.get('run_simulation', False):
        with st.spinner('🔄 Menjalankan simulasi...'):
            config = {
                'total_meja': total_meja,
                'mahasiswa_per_meja': mahasiswa_per_meja,
                'random_seed': 42,
                'stage1_workers': stage1_workers,
                'stage2_workers': stage2_workers,
                'stage3_workers': stage3_workers,
                'stage1_min': stage1_min,
                'stage1_max': stage1_max,
                'stage2_min': stage2_min,
                'stage2_max': stage2_max,
                'stage3_min': stage3_min,
                'stage3_max': stage3_max,
                'batch_min': batch_min,
                'batch_max': batch_max
            }
            
            finish1, finish2, finish3, batches = simulate_piket(config)
            results = analyze_results(config, finish1, finish2, finish3, batches)
        
        st.session_state.results = results
        st.session_state.config = config
    
    # Tampilkan hasil jika ada
    if 'results' in st.session_state:
        results = st.session_state.results
        config = st.session_state.config
        TOTAL_OMPRENG = config['total_meja'] * config['mahasiswa_per_meja']
        
        # Hitung waktu selesai
        total_time = results['total_time']
        menit = int(total_time // 60)
        detik = int(total_time % 60)
        selesai_jam = 7 + menit // 60
        selesai_menit = menit % 60
        
        # ======================
        # METRICS SECTION
        # ======================
        st.markdown('<div class="sub-header">📊 Ringkasan Hasil Simulasi</div>', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="⏱️ Waktu Total",
                value=f"{menit}m {detik}s",
                delta=f"{total_time:.1f} detik"
            )
        
        with col2:
            st.metric(
                label="🕐 Perkiraan Selesai",
                value=f"{selesai_jam:02d}.{selesai_menit:02d} WIB"
            )
        
        with col3:
            st.metric(
                label="🍚 Total Porsi",
                value=f"{TOTAL_OMPRENG}"
            )
        
        with col4:
            st.metric(
                label="🔄 Rata-rata Batch",
                value=f"{results['avg_batch']:.2f}"
            )
        
        col5, col6, col7 = st.columns(3)
        
        with col5:
            st.metric(
                label="⚠️ Bottleneck",
                value=results['bottleneck'],
                delta=f"{results['bottleneck_util']:.1f}% utilisasi"
            )
        
        with col6:
            st.metric(
                label="📈 Utilisasi Rata-rata",
                value=f"{(results['stage1_util'] + results['stage2_util'] + results['stage3_util']) / 3:.1f}%"
            )
        
        with col7:
            st.metric(
                label="👥 Total Petugas",
                value=f"{config['stage1_workers'] + config['stage2_workers'] + config['stage3_workers']}"
            )
        
        # ======================
        # TABS SECTION
        # ======================
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📈 Visualisasi",
            "📋 Detail Meja",
            "📊 Utilisasi",
            "💡 Rekomendasi",
            "💾 Data Lengkap"
        ])
        
        with tab1:
            st.markdown("### Visualisasi Hasil Simulasi")
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig1 = plot_meja_timeline(results['df_meja'])
                st.plotly_chart(fig1, use_container_width=True)
            
            with col2:
                fig2 = plot_batch_distribution(results['batch_sizes'])
                st.plotly_chart(fig2, use_container_width=True)
            
            st.plotly_chart(plot_gantt_chart(results['df_timeline']), use_container_width=True)
        
        with tab2:
            st.markdown("### 📋 Detail Kesiapan Meja")
            
            # Tampilkan 5 meja pertama dan terakhir
            df_display = pd.concat([
                results['df_meja'].head(5),
                pd.DataFrame([{'meja': '...', 'waktu': 0, 'menit': 0, 'detik': 0, 'jam': 0, 'menit_jam': 0}]),
                results['df_meja'].tail(5)
            ], ignore_index=True)
            
            st.dataframe(
                df_display[['meja', 'menit', 'detik', 'jam', 'menit_jam']].rename(columns={
                    'meja': 'Meja',
                    'menit': 'Menit',
                    'detik': 'Detik',
                    'jam': 'Jam',
                    'menit_jam': 'Menit Jam'
                }),
                hide_index=True,
                use_container_width=True
            )
            
            # Statistik meja
            st.markdown("#### Statistik Kesiapan Meja")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Meja Pertama Siap",
                    f"{results['df_meja']['menit'].iloc[0]}m {results['df_meja']['detik'].iloc[0]}s",
                    f"Jam {results['df_meja']['jam'].iloc[0]:02d}.{results['df_meja']['menit_jam'].iloc[0]:02d}"
                )
            
            with col2:
                median_time = results['df_meja']['waktu'].median() / 60
                st.metric(
                    "Median Waktu Siap",
                    f"{median_time:.1f} menit"
                )
            
            with col3:
                st.metric(
                    "Meja Terakhir Siap",
                    f"{results['df_meja']['menit'].iloc[-1]}m {results['df_meja']['detik'].iloc[-1]}s",
                    f"Jam {results['df_meja']['jam'].iloc[-1]:02d}.{results['df_meja']['menit_jam'].iloc[-1]:02d}"
                )
        
        with tab3:
            st.markdown("### 📊 Utilisasi Petugas Piket per Tahap")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                fig_util = plot_utilization_chart(results['df_utilization'])
                st.plotly_chart(fig_util, use_container_width=True)
            
            with col2:
                st.markdown("#### Detail Utilisasi")
                for _, row in results['df_utilization'].iterrows():
                    color = "🟢" if row['Utilisasi'] < 70 else "🟡" if row['Utilisasi'] < 90 else "🔴"
                    st.markdown(f"**{color} {row['Tahap']}**")
                    # PERBAIKAN: Konversi ke skala 0-1
                    st.progress(min(1.0, row['Utilisasi'] / 100))
                    st.caption(f"{row['Utilisasi']:.1f}%")
                    st.markdown("---")
            
            # Analisis bottleneck
            st.markdown("### ⚠️ Analisis Bottleneck")
            bottleneck_stage = results['bottleneck']
            bottleneck_util = results['bottleneck_util']
            
            if bottleneck_util > 90:
                st.error(f"**{bottleneck_stage}** mengalami bottleneck dengan utilisasi **{bottleneck_util:.1f}%**")
                st.info("💡 **Saran**: Pertimbangkan menambah 1 petugas di tahap ini untuk mengurangi bottleneck.")
            elif bottleneck_util > 75:
                st.warning(f"**{bottleneck_stage}** mendekati kapasitas dengan utilisasi **{bottleneck_util:.1f}%**")
                st.info("💡 **Saran**: Monitor kinerja tahap ini. Pertimbangkan redistribusi beban jika diperlukan.")
            else:
                st.success(f"Sistem berjalan optimal. Utilisasi tertinggi: **{bottleneck_util:.1f}%**")
        
        with tab4:
            st.markdown("### 💡 Rekomendasi Optimasi")
            
            bottleneck_stage = results['bottleneck']
            bottleneck_util = results['bottleneck_util']
            
            if bottleneck_util > 90:
                st.error(f"**⚠️ Bottleneck Terdeteksi di {bottleneck_stage}**")
                
                if "Tahap 3" in bottleneck_stage:
                    st.markdown("""
                    #### 🎯 Rekomendasi Alokasi Petugas Piket:
                    - **Opsi 1**: 3-2-2 (Tambah 1 di Tahap 3) → Total 8 petugas
                    - **Opsi 2**: 2-2-3 (Redistribusi dari Tahap 1 ke Tahap 3)
                    
                    #### 📋 Strategi Operasional:
                    1. **Standardisasi Batch**: Targetkan 6 ompreng/batch di Tahap 2
                    2. **Zonasi Meja**: Bagi 60 meja menjadi 3 zona (20 meja/zona)
                    3. **Prioritas**: Fokus selesaikan batch besar terlebih dahulu
                    """)
                elif "Tahap 1" in bottleneck_stage:
                    st.markdown("""
                    #### 🎯 Rekomendasi Alokasi Petugas Piket:
                    - **Opsi 1**: 4-2-1 (Tambah 1 di Tahap 1) → Total 8 petugas
                    - **Opsi 2**: 3-3-1 (Redistribusi dari Tahap 3 ke Tahap 1)
                    
                    #### 📋 Strategi Operasional:
                    1. **Prep Awal**: Siapkan lauk di beberapa wadah sebelum 07.00
                    2. **Assembly Line**: Buat stasiun khusus untuk setiap jenis lauk
                    3. **Batch Processing**: Proses beberapa ompreng sekaligus
                    """)
                else:
                    st.markdown("""
                    #### 🎯 Rekomendasi Alokasi Petugas Piket:
                    - **Opsi 1**: 3-3-1 (Tambah 1 di Tahap 2) → Total 8 petugas
                    - **Opsi 2**: 2-4-1 (Redistribusi dari Tahap 3 ke Tahap 2)
                    
                    #### 📋 Strategi Operasional:
                    1. **Optimasi Rute**: Rencanakan jalur terpendek untuk mengangkat
                    2. **Batch Size**: Gunakan batch 6-7 ompreng untuk efisiensi
                    3. **Staging Area**: Siapkan area transit dekat meja
                    """)
            else:
                st.success("✅ **Sistem Sudah Optimal!**")
                st.markdown("""
                #### 📊 Kinerja Saat Ini:
                - Utilisasi seimbang di semua tahap
                - Tidak ada bottleneck signifikan
                - Waktu penyelesaian dalam target
                
                #### 💡 Tips Pemeliharaan:
                1. **Monitor Rutin**: Lakukan simulasi berkala untuk deteksi dini bottleneck
                2. **Fleksibilitas**: Siapkan 1-2 petugas cadangan untuk kondisi darurat
                3. **Standardisasi**: Dokumentasikan prosedur terbaik untuk konsistensi
                """)
            
            # Perbandingan alokasi
            st.markdown("### 📊 Perbandingan Alokasi Petugas Piket")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**Alokasi Saat Ini**")
                st.metric("Tahap 1", config['stage1_workers'])
                st.metric("Tahap 2", config['stage2_workers'])
                st.metric("Tahap 3", config['stage3_workers'])
                st.metric("Total", config['stage1_workers'] + config['stage2_workers'] + config['stage3_workers'])
            
            with col2:
                st.markdown("**Rekomendasi Optimal**")
                if "Tahap 3" in bottleneck_stage and bottleneck_util > 90:
                    st.metric("Tahap 1", config['stage1_workers'] - 1, "-1")
                    st.metric("Tahap 2", config['stage2_workers'])
                    st.metric("Tahap 3", config['stage3_workers'] + 1, "+1")
                    st.metric("Total", config['stage1_workers'] + config['stage2_workers'] + config['stage3_workers'])
                elif "Tahap 1" in bottleneck_stage and bottleneck_util > 90:
                    st.metric("Tahap 1", config['stage1_workers'] + 1, "+1")
                    st.metric("Tahap 2", config['stage2_workers'])
                    st.metric("Tahap 3", config['stage3_workers'] - 1, "-1")
                    st.metric("Total", config['stage1_workers'] + config['stage2_workers'] + config['stage3_workers'])
                else:
                    st.metric("Tahap 1", config['stage1_workers'])
                    st.metric("Tahap 2", config['stage2_workers'])
                    st.metric("Tahap 3", config['stage3_workers'])
                    st.metric("Total", config['stage1_workers'] + config['stage2_workers'] + config['stage3_workers'])
            
            with col3:
                st.markdown("**Estimasi Perbaikan**")
                if bottleneck_util > 90:
                    st.metric("Pengurangan Waktu", f"~{int(menit * 0.15)} menit", f"-15%")
                    st.metric("Utilisasi Maks", f"~{min(90, bottleneck_util - 15):.0f}%", f"-15%")
                else:
                    st.metric("Status", "Optimal", "✓")
        
        with tab5:
            st.markdown("### 💾 Data Lengkap Simulasi")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Timeline Per Ompreng")
                st.dataframe(results['df_timeline'].head(20), use_container_width=True)
                st.caption(f"Menampilkan 20 dari {len(results['df_timeline'])} ompreng")
            
            with col2:
                st.markdown("#### Kesiapan Per Meja")
                st.dataframe(results['df_meja'][['meja', 'waktu', 'menit', 'detik']], use_container_width=True)
                st.caption(f"Total {len(results['df_meja'])} meja")
            
            st.markdown("#### Distribusi Ukuran Batch")
            batch_dist = pd.Series(results['batch_sizes']).value_counts().sort_index()
            st.bar_chart(batch_dist)
            
            st.markdown("#### Statistik Batch")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Jumlah Batch", len(results['batch_sizes']))
            with col2:
                st.metric("Rata-rata", f"{results['avg_batch']:.2f}")
            with col3:
                st.metric("Minimum", min(results['batch_sizes']))
            with col4:
                st.metric("Maksimum", max(results['batch_sizes']))
        
        # ======================
        # FOOTER
        # ======================
        st.markdown("---")
        st.markdown("""
        <div style='text-align: center; color: #666;'>
        <small>
        🍚 Simulasi Prasmanan di Kantin IT Del - Dibuat dengan Streamlit & Plotly - 
        Estimasi berdasarkan model simulasi diskrit - Yessa Situmeang 11S25041
        </small>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    if 'run_simulation' not in st.session_state:
        st.session_state.run_simulation = False
    main()