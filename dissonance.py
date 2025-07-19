import sys
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QPushButton, QListWidget, QLabel, 
                             QListWidgetItem, QAbstractItemView)
from PyQt5.QtCore import Qt

class DissonanceAnalyzer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.selected_notes = set()
        self.num_overtones = 8
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle('Musical Dissonance Analyzer')
        self.setGeometry(100, 100, 800, 600)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QHBoxLayout(central_widget)
        
        left_panel = QVBoxLayout()
        left_panel.addWidget(QLabel("Select Notes (Context):"))
        
        self.note_selector = QListWidget()
        self.note_selector.setSelectionMode(QAbstractItemView.MultiSelection)
        self.populate_note_selector()
        left_panel.addWidget(self.note_selector)
        
        self.analyze_btn = QPushButton("Analyze Dissonance")
        self.analyze_btn.clicked.connect(self.analyze_dissonance)
        left_panel.addWidget(self.analyze_btn)
        
        right_panel = QVBoxLayout()
        right_panel.addWidget(QLabel("Notes Ordered by Least Dissonance:"))
        
        self.results_list = QListWidget()
        right_panel.addWidget(self.results_list)
        
        layout.addLayout(left_panel, 1)
        layout.addLayout(right_panel, 1)
    
    def populate_note_selector(self):
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        
        for midi_note in range(21, 109):
            octave = (midi_note - 12) // 12
            note_name = note_names[midi_note % 12]
            display_name = f"{note_name}{octave} ({midi_note})"
            
            item = QListWidgetItem(display_name)
            item.setData(Qt.UserRole, midi_note)
            self.note_selector.addItem(item)
    
    def get_frequency(self, note, tuning=440.0):
        return tuning * 2**((note - 69) / 12)
    
    def get_harmonics(self, fundamental_freq, num_overtones):
        harmonics = np.arange(1, num_overtones + 2)
        return fundamental_freq * harmonics, 1.0 / harmonics
    
    def sethares_dissonance(self, f1, f2, a1, a2):
        mask = f1 > f2
        f1_adj = np.where(mask, f2, f1)
        f2_adj = np.where(mask, f1, f2)
        a1_adj = np.where(mask, a2, a1)
        a2_adj = np.where(mask, a1, a2)
        
        zero_mask = f1_adj == 0
        ratio = np.divide(f2_adj, f1_adj, out=np.ones_like(f1_adj), where=~zero_mask)
        
        b1, b2, s1, s2 = 3.5, 5.75, 0.0207, 18.96
        s = s1 * f1_adj + s2
        
        diss = a1_adj * a2_adj * (np.exp(-b1 * s * (ratio - 1)) - np.exp(-b2 * s * (ratio - 1)))
        return np.where(zero_mask | (diss < 0), 0, diss)
    
    def harmonic_dissonance(self, freq1, freq2, num_overtones):
        freqs1, amps1 = self.get_harmonics(freq1, num_overtones)
        freqs2, amps2 = self.get_harmonics(freq2, num_overtones)
        
        freqs1_mesh, freqs2_mesh = np.meshgrid(freqs1, freqs2, indexing='ij')
        amps1_mesh, amps2_mesh = np.meshgrid(amps1, amps2, indexing='ij')
        
        dissonance_matrix = self.sethares_dissonance(freqs1_mesh, freqs2_mesh, amps1_mesh, amps2_mesh)
        return np.sum(dissonance_matrix)
    
    def human_dissonance(self, freq1, freq2, num_overtones, leeway=1.02, max_samples=100):
        min_diss = float('inf')
        freq_min = freq2 / leeway
        freq_max = freq2 * leeway
        
        for i in range(max_samples + 1):
            test_freq = freq_min + (freq_max - freq_min) * i / max_samples
            diss = self.harmonic_dissonance(freq1, test_freq, num_overtones)
            min_diss = min(min_diss, diss)
        
        return min_diss
    
    def analyze_dissonance(self):
        selected_items = self.note_selector.selectedItems()
        if not selected_items:
            return
            
        selected_notes = [item.data(Qt.UserRole) for item in selected_items]
        
        min_note = min(selected_notes) - 12
        max_note = max(selected_notes) + 12
        
        results = []
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        
        for candidate_note in range(min_note, max_note + 1):
            if candidate_note in selected_notes:
                continue
                
            candidate_freq = self.get_frequency(candidate_note)
            total_dissonance = 0
            
            for context_note in selected_notes:
                context_freq = self.get_frequency(context_note)
                total_dissonance += self.human_dissonance(context_freq, candidate_freq, self.num_overtones)
            
            octave = (candidate_note - 12) // 12
            note_name = note_names[candidate_note % 12]
            display_name = f"{note_name}{octave} ({candidate_note})"
            
            results.append((total_dissonance, display_name))
        
        results.sort(key=lambda x: x[0])
        
        self.results_list.clear()
        for dissonance, name in results:
            item_text = f"{name} - Dissonance: {dissonance:.4f}"
            self.results_list.addItem(item_text)

app = QApplication(sys.argv)
window = DissonanceAnalyzer()
window.show()
sys.exit(app.exec_())