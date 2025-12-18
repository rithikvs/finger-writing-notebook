# ✍️ Air Writing Notebook

A real-time hand gesture-based air writing application that allows you to write and draw in the air using your webcam. Write notes, create sketches, and save your work—all without touching a screen!

## ✨ Features

### Core Functionality
- **Air Writing**: Write in the air using your index finger
- **Multi-Color Support**: Choose from blue, green, and red colors
- **Eraser Tool**: Erase specific parts of your drawing
- **Clear Canvas**: Start fresh with a single gesture
- **Real-time Hand Tracking**: Smooth and stable hand landmark detection

### Advanced Features
- **Undo/Redo**: Revert or reapply your actions with gestures
  - Fist → Peace sign (fingers apart) = Undo
  - Fist → Open hand (all 5 fingers) = Redo
- **Multiple Export Formats**:
  - PNG images (default)
  - JPEG images
  - PDF documents
- **Auto-Save**: Timestamp-based file naming
- **Smart Gesture Detection**: Stabilized gesture recognition to prevent accidental breaks in strokes

## 🎮 Gesture Controls

| Gesture | Action |
|---------|--------|
| ✋ Index finger extended (thumb & others closed) | Write/Draw |
| 👊 Fist → ✌️ Peace sign (fingers apart) | Undo last action |
| 👊 Fist → 🖐️ Open hand (all 5 fingers) | Redo action |
| ☝️✌️ Index + Middle together (pinched) | Save note |
| ☝️ Index finger hover on button | Select color/eraser/clear |

## 🎨 UI Buttons

- **Blue/Green/Red**: Change drawing color
- **Erase**: Switch to eraser mode
- **Clear**: Clear entire canvas
- **Save**: Save current canvas as PNG
- **X**: Close application

## ⌨️ Keyboard Shortcuts

- `S` - Save as PNG
- `P` - Save as PDF
- `J` - Save as JPEG
- `Q` - Quit application

## 🚀 Installation

### Prerequisites
- Python 3.7 or higher
- Webcam

### Setup

1. Clone this repository:
```bash
git clone <repository-url>
cd writing
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

## 💻 Usage

Run the application:
```bash
python main.py
```

### Getting Started
1. Position yourself in front of the webcam
2. Extend your index finger (keeping other fingers closed) to start writing
3. Hover over color buttons to change colors
4. Use gestures to undo/redo or save your work
5. All saved files are stored in the `saved_notes/` directory

## 📁 Project Structure

```
writing/
├── main.py              # Main application file
├── saved_notes/         # Directory for saved drawings
├── requirements.txt     # Python dependencies
└── README.md           # Project documentation
```

## 🛠️ Technical Details

### Technologies Used
- **OpenCV**: Real-time video capture and image processing
- **MediaPipe**: Hand landmark detection and tracking
- **NumPy**: Array operations and canvas manipulation
- **Pillow (PIL)**: Image format conversion
- **ReportLab**: PDF generation

### Key Features Implementation
- Hand gesture recognition with stability thresholds
- Smoothed cursor movement for cleaner lines
- Canvas state management with undo/redo history
- Multi-format export support

## 📸 Output

Saved files are automatically timestamped and stored in `saved_notes/`:
- Format: `airwriting_YYYYMMDD_HHMMSS.{png|jpg|pdf}`
- Example: `airwriting_20251218_143025.png`

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest new features
- Submit pull requests

## 📝 License

This project is open source and available under the MIT License.

## 🙏 Acknowledgments

- MediaPipe for powerful hand tracking
- OpenCV community for computer vision tools

## 📧 Contact

For questions or feedback, please open an issue on GitHub.

---

**Enjoy writing in the air!** ✨✍️
