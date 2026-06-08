# Box to Search (OCR Tool)

A premium Windows-integrated screenshot OCR and Translation utility built with Python and CustomTkinter. Select any region on your screen using a keyboard shortcut, instantly extract text, translate it, perform visual web searches, or have it read aloud.

---

## Features
- **Global Shortcut Capture**: Press `Ctrl+Shift+X` (configurable) from anywhere to select a screen area.
- **Advanced OCR**: Dual-mode extraction featuring Windows native offline OCR (using `WinRT`) and an online fallback (OCR.space API).
- **Instant Translation**: Translate extracted text on the fly to Spanish, French, German, Japanese, Chinese, and other languages.
- **Sleek UI Design**: Beautiful dark mode card interface matching premium design standards.
- **File Browser / Standalone Mode**: Drag/drop container supporting local file browsing (`.png`, `.jpg`, `.jpeg`, `.webp`), letting the app function as a standalone OCR tool.
- **Google Lens Visual Search**: Instantly upload the crop to perform Google Lens visual searches.
- **Text to Speech**: Read the extracted text aloud.
- **Run on System Startup**: Toggle startup registration under `HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run`.

---

## Prerequisites
- **Operating System**: Windows 10 or 11 (required for Windows native WinRT OCR and startup registry integration).
- **Python**: Python 3.10 or higher.

---

## Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone <https://github.com/PrinceSrinivasan/Box-to-Search.git>
   cd "rectangle to search"
   ```

2. **Install the dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   python app.py
   ```
   *Note: The app will minimize to your system tray. Press `Ctrl+Shift+X` to start capturing.*

---

## Compiling to a Standalone `.exe`
To compile the project into a single, portable executable file:
1. Ensure PyInstaller is installed:
   ```bash
   pip install pyinstaller
   ```
2. Build the application using the pre-configured `.spec` file:
   ```bash
   pyinstaller -y BoxToSearch.spec
   ```
3. Locate the standalone binary under the `dist/` directory:
   - `dist/BoxToSearch.exe`
