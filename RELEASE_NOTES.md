# Release Notes: Box to Search (v1.0.0)

**Box to Search** is a premium, Windows-integrated screenshot OCR (Optical Character Recognition) and translation desktop application. Designed with modern aesthetics and power-user workflows in mind, it allows you to capture any area of your screen, extract text instantly, translate it on-the-fly, perform Google Lens visual searches, or read it aloud.

---

## 🌟 Key Features

### 🖥️ 1. Screen Capture & Overlay System
* **Global Shortcut Activation**: Instantly trigger screen selection with a customizable global keyboard shortcut (default: `Ctrl+Shift+X`).
* **Sleek Overlay**: Capture selected regions via a pixel-precise, smooth overlay interface. Cancel anytime with a simple right-click.

### 🔍 2. Advanced Dual-Mode OCR Engine
* **Offline Mode (Native WinRT)**: Leverages Windows 10/11 built-in OCR capabilities for private, offline extraction with high efficiency.
* **Online Mode (OCR.space API)**: Leverages the OCR.space API to handle more complex layouts or web fonts.
* **Intelligent Preprocessing Pipeline**: Concurrently processes the image with three distinct recipes (Standard Lanczos resizing, low-contrast thresholding at 120, and high-contrast thresholding at 200) to ensure high-accuracy character recognition on small or stylized text.
* **Spatial Reconstruction**: Intelligently groups and aligns recognized text segments horizontally and vertically to reconstruct the original reading flow.

### 🌐 3. Seamless translation
* **Google Translate Integration**: Built on top of Google Translate (via `deep-translator`) with automatic source language detection.
* **Interactive Dropdown**: Select target languages on-the-fly directly inside the results interface. Supports a wide array of global languages (Spanish, French, German, Japanese, Traditional/Simplified Chinese, Hindi, Russian, etc.).

### 🖼️ 4. Standalone & Drag-and-Drop Mode
* **Universal File Compatibility**: Supports opening or drag-dropping image formats directly (`.png`, `.jpg`, `.jpeg`, `.webp`).
* **Standalone Operation**: Acts as an image reader/OCR tool, eliminating the need to capture a screenshot if you already have the file.

### 🔊 5. Accessibility & Web Search
* **Text-to-Speech (TTS)**: Built-in Microsoft Speech API (SAPI) reader reads extracted text aloud with simple play/stop controls.
* **Google Lens Web Search**: Instantly uploads the crop to `tmpfiles.org` (secure, temporary hosting) to launch a Google Lens visual search in your default web browser.

### ⚙️ 6. Premium Settings & Windows Integration
* **Interactive Hotkey Recording**: Change your global hotkey inside the settings menu by pressing the keys you want to bind.
* **Startup on Boot**: Registers application launcher key into Windows Registry (`HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run`) with a single click toggle.
* **System Tray Minimization**: Runs in the background with custom tray notifications to maximize workspace real estate.

---

## 🛠️ Technical Stack & Libraries
* **GUI Framework**: [CustomTkinter](https://github.com/tomsimkina/customtkinter) for a sleek, dark-themed responsive UI.
* **OCR Technologies**: 
  * Windows Native Windows RunTime OCR API (`winrt`).
  * OCR.space REST API (`requests`).
* **Translation**: `deep-translator` library.
* **Keyboard Hotkeys**: `pynput` for cross-platform global hotkeys.
* **TTS System**: Windows Component Object Model API via `pywin32` (`win32com.client`).
* **Compilation**: `PyInstaller` for producing single, portable binary packaging.

---

## 📋 System Requirements
* **Operating System**: Windows 10 or 11 (required for WinRT Native OCR API and registry startup entries).
* **Python Version**: Python 3.10 or higher.

---

## 🚀 Getting Started

### 1. Installation
Clone the repository and install all required dependencies:
```bash
git clone https://github.com/PrinceSrinivasan/Box-to-Search.git
cd "Box to Search"
pip install -r requirements.txt
```

### 2. Execution
Run the app using the python interpreter:
```bash
python app.py
```
*Note: The app will minimize directly to your system tray. Tap **`Ctrl+Shift+X`** to start capturing your screen.*

### 3. Packaging into Standalone `.exe`
Compile the project into a single, dependency-free executable using the pre-configured `.spec` file:
```bash
pip install pyinstaller
pyinstaller -y BoxToSearch.spec
```
Locate your output binary at `dist/BoxToSearch.exe`.

---

## 🎨 UI Highlight: Dark Theme Aesthetics
The app features custom design tokens, Harmonious dark color themes (`#0c0c0c` and `#151518`), smooth accent colors (`#2563eb`), clear state icons (Success, Warning, Running), and a modern card-based column layout:
1. **Left Card (Image)**: Preview of the captured image crop with responsive action buttons (Search on Web, Save Image, Read Extracted Text).
2. **Right Top Card (Extracted Text)**: Area displaying high-fidelity extracted OCR text with Copy and Retry controls.
3. **Right Bottom Card (Translate)**: Live translation frame with an inline language picker and instant Copy option.
