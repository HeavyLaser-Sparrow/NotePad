import sys
import os # Added for path manipulation
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTextEdit, QFileDialog, QAction, QTabWidget, QWidget,
                             QVBoxLayout, QToolBar, QMessageBox, QComboBox)
from PyQt5.QtGui import QFont, QColor, QSyntaxHighlighter, QTextCharFormat, QKeySequence
from PyQt5.QtCore import Qt, QRegularExpression


class TextHighlighter(QSyntaxHighlighter):
    def __init__(self, parent, file_extension):
        super(TextHighlighter, self).__init__(parent)
        self.highlightingRules = []
        self.applyRules(file_extension) # Changed to call a method

    # Method to set rules based on extension
    def applyRules(self, file_extension):
        self.highlightingRules = [] # Clear existing rules
        self.file_extension = file_extension

        if self.file_extension == ".py":
            keywordFormat = QTextCharFormat()
            keywordFormat.setForeground(QColor("cyan")) # Changed color for visibility
            keywordFormat.setFontWeight(QFont.Bold)
            keywords = [
                "False", "None", "True", "and", "as", "assert", "async", "await",
                "break", "class", "continue", "def", "del", "elif", "else", "except",
                "finally", "for", "from", "global", "if", "import", "in", "is",
                "lambda", "nonlocal", "not", "or", "pass", "raise", "return", "try",
                "while", "with", "yield"
            ]
            self.highlightingRules += [(QRegularExpression(f"\\b{keyword}\\b"), keywordFormat) for keyword in keywords]

            # Example: Add comments highlighting
            commentFormat = QTextCharFormat()
            commentFormat.setForeground(QColor("green"))
            self.highlightingRules.append((QRegularExpression("#[^\n]*"), commentFormat))

            # Example: Add string highlighting
            stringFormat = QTextCharFormat()
            stringFormat.setForeground(QColor("magenta"))
            self.highlightingRules.append((QRegularExpression("\".*\""), stringFormat))
            self.highlightingRules.append((QRegularExpression("'.*'"), stringFormat))

        # Rehighlight the entire document after rules change
        self.rehighlight()

    def highlightBlock(self, text):
        for pattern, fmt in self.highlightingRules:
            # Use QRegularExpressionMatchIterator for potentially better performance/correctness
            iterator = pattern.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)
        # Apply default format to areas not covered by rules (optional, but good practice)
        # self.setCurrentBlockState(0) # Reset state if using multi-line highlighting


class TextEditor(QWidget):
    def __init__(self, parent=None):
        super(TextEditor, self).__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0) # Remove layout margins for tighter fit
        self.text = QTextEdit(self)
        self.text.setFont(QFont("Roboto Mono", 12))
        # Adjusted style slightly for better visual separation if needed
        self.text.setStyleSheet("QTextEdit { background-color: #1E1E1E; color: #E0E0E0; padding: 10px; border: none; }")
        self.path = ""
        self.file_extension = ".txt" # Default to .txt
        # Initialize highlighter immediately with default extension
        self.highlighter = TextHighlighter(self.text.document(), self.file_extension)
        layout.addWidget(self.text)
        self.setLayout(layout)
        self.isModified = False
        self.text.textChanged.connect(self.markUnsaved)

    # Renamed for clarity and updated logic
    def setFileDetails(self, path):
        self.path = path
        _, ext = os.path.splitext(path)
        self.file_extension = ext.lower() if ext else ".txt" # Handle no extension case
        # Update highlighter rules based on the actual file extension
        if self.highlighter:
             self.highlighter.applyRules(self.file_extension)
        self.isModified = False # Reset modified status after load/save

    def markUnsaved(self):
        if not self.isModified:
            self.isModified = True
            # Find the QTabWidget correctly - safer approach
            tab_widget = self.parentWidget()
            if tab_widget and isinstance(tab_widget, QTabWidget):
                index = tab_widget.indexOf(self) # Index of this TextEditor widget
                if index != -1: # Check if the widget is actually in the tab widget
                    currentText = tab_widget.tabText(index)
                    if not currentText.endswith(" *"):
                        tab_widget.setTabText(index, f"{currentText} *")

    # Added method to update highlighter externally (e.g., from combobox change)
    def updateSyntaxHighlighting(self, extension):
         self.file_extension = extension
         if self.highlighter:
              self.highlighter.applyRules(self.file_extension)


class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Google Chromebook Text Clone")
        self.resize(800, 600)
        # Main window background - tabs will cover most of it
        self.setStyleSheet("QMainWindow { background-color: #181818; }")

        self.tabs = QTabWidget(self)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.closeTab)
        self.tabs.setMovable(True)
        # Modern tab styling (example, adjust as needed)
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border-top: 1px solid #444;
                background-color: #1E1E1E; /* Pane background */
            }
            QTabBar::tab {
                background: #2A2A2A;
                color: #E0E0E0;
                padding: 8px 15px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                border: 1px solid #444;
                border-bottom: none; /* Remove bottom border for non-selected */
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #1E1E1E; /* Match pane background */
                font-weight: bold;
                border-bottom: 1px solid #1E1E1E; /* Hide bottom border visually */
            }
            QTabBar::tab:!selected:hover {
                background: #3A3A3A;
            }
            QTabBar::close-button {
                /* Add styling for close button if desired */
                subcontrol-position: right;
            }
            QTabBar::close-button:hover {
                background: #555;
            }
        """)
        self.setCentralWidget(self.tabs)
        self.createActions()
        self.createToolbar()
        self.createShortcuts()
        self.newFile() # Start with one empty tab

    def createActions(self):
        self.newAction = QAction("New", self)
        self.newAction.triggered.connect(self.newFile)

        self.openAction = QAction("Open", self)
        self.openAction.triggered.connect(self.openFile)

        self.saveAction = QAction("Save", self)
        self.saveAction.triggered.connect(self.saveFile)

        self.saveAsAction = QAction("Save As", self)
        self.saveAsAction.triggered.connect(self.saveFileAs)

        # Connect to a helper method to handle closing the current tab safely
        self.closeAction = QAction("Close Tab", self)
        self.closeAction.triggered.connect(self.closeCurrentTab)

    def createToolbar(self):
        toolbar = QToolBar("Main Toolbar", self)
        toolbar.setStyleSheet("QToolBar { background-color: #1E1E1E; border: none; padding: 5px; } "
                              "QToolButton { color: #E0E0E0; padding: 3px; } "
                              "QToolButton:hover { background-color: #3A3A3A; }")
        self.addToolBar(Qt.TopToolBarArea, toolbar) # Specify area

        # File Type ComboBox setup
        self.fileTypeComboBox = QComboBox(self)
        self.fileTypeComboBox.addItems([".txt", ".py"]) # Add more types as needed
        self.fileTypeComboBox.setStyleSheet("QComboBox { background-color: #2A2A2A; color: #E0E0E0; border-radius: 3px; padding: 3px 5px; }")
        # Connect signal to update syntax when selection changes
        self.fileTypeComboBox.currentTextChanged.connect(self.updateCurrentTabSyntax)

        toolbar.addAction(self.newAction)
        toolbar.addAction(self.openAction)
        toolbar.addAction(self.saveAction)
        toolbar.addAction(self.saveAsAction)
        toolbar.addAction(self.closeAction)
        toolbar.addSeparator()
        toolbar.addWidget(self.fileTypeComboBox)


    def createShortcuts(self):
        self.newAction.setShortcut(QKeySequence.New) # Standard shortcuts
        self.openAction.setShortcut(QKeySequence.Open)
        self.saveAction.setShortcut(QKeySequence.Save)
        self.saveAsAction.setShortcut(QKeySequence.SaveAs)
        self.closeAction.setShortcut(QKeySequence.Close) # Typically closes window, but we use Ctrl+W for tab

        # Add specific Ctrl+W for closing tab
        self.closeTabShortcut = QAction("Close Tab Shortcut", self)
        self.closeTabShortcut.setShortcut(QKeySequence("Ctrl+W"))
        self.closeTabShortcut.triggered.connect(self.closeCurrentTab)
        self.addAction(self.closeTabShortcut) # Add to window actions


    def newFile(self):
        editor = TextEditor(self.tabs) # Parent should be the tabs widget
        default_ext = self.fileTypeComboBox.currentText()
        editor.updateSyntaxHighlighting(default_ext) # Set initial syntax based on combobox
        
        # Find an available "Untitled" name
        untitled_count = 1
        tab_name = "Untitled"
        while self.findTabByName(f"{tab_name} *") is not None or self.findTabByName(tab_name) is not None:
            untitled_count += 1
            tab_name = f"Untitled {untitled_count}"

        index = self.tabs.addTab(editor, tab_name)
        self.tabs.setCurrentIndex(index)
        # No path yet, so mark as modified immediately to get the "*"
        editor.markUnsaved()


    def findTabByName(self, name):
        for i in range(self.tabs.count()):
            if self.tabs.tabText(i) == name:
                return i
        return None

    def openFile(self):
        # Define filters based on supported types
        filters = "Text Files (*.txt);;Python Files (*.py);;All Files (*)"
        path, _ = QFileDialog.getOpenFileName(self, "Open File", "", filters)

        if path:
            # Check if file is already open
            for i in range(self.tabs.count()):
                widget = self.tabs.widget(i)
                if isinstance(widget, TextEditor) and widget.path == path:
                    self.tabs.setCurrentIndex(i)
                    return # Switch to existing tab

            try:
                with open(path, "r", encoding='utf-8') as file: # Specify encoding
                    content = file.read()

                editor = TextEditor(self.tabs) # Parent should be tabs
                editor.text.setText(content)
                editor.setFileDetails(path) # This sets path, extension, and highlighter

                # Update combobox if opened file type is different and supported
                if editor.file_extension in [".txt", ".py"]: # Check if extension is in combobox items
                   if self.fileTypeComboBox.currentText() != editor.file_extension:
                       self.fileTypeComboBox.setCurrentText(editor.file_extension)
                       # Note: setCurrentText will trigger updateCurrentTabSyntax automatically

                index = self.tabs.addTab(editor, os.path.basename(path))
                self.tabs.setCurrentIndex(index)
                editor.isModified = False # File is just opened, not modified yet

            except Exception as e:
                QMessageBox.critical(self, "Error Opening File", f"Could not open file:\n{e}")


    def saveFile(self):
        editor = self.currentEditor()
        if not editor: # Check if there is an active editor
            return

        # If editor has no path (it's a new file), call saveFileAs
        if not editor.path:
            self.saveFileAs()
        else:
            try:
                with open(editor.path, "w", encoding='utf-8') as file: # Specify encoding
                    file.write(editor.text.toPlainText())
                editor.isModified = False # Mark as saved
                # Update tab text to remove "*"
                index = self.tabs.currentIndex()
                self.tabs.setTabText(index, os.path.basename(editor.path))
            except Exception as e:
                 QMessageBox.critical(self, "Error Saving File", f"Could not save file:\n{e}")


    def saveFileAs(self):
        editor = self.currentEditor()
        if not editor: # Check if there is an active editor
            return

        # Suggest filename based on current tab text (without '*')
        current_tab_text = self.tabs.tabText(self.tabs.currentIndex()).replace(" *", "")
        # Suggest directory based on current path or default directory
        start_dir = os.path.dirname(editor.path) if editor.path else ""

        # Use the current file type combobox selection to set the default filter
        selected_filter = f"{editor.file_extension.upper()} Files (*{editor.file_extension})"
        filters = f"Text Files (*.txt);;Python Files (*.py);;All Files (*)"
        
        path, selected_filter_out = QFileDialog.getSaveFileName(
            self,
            "Save File As",
            os.path.join(start_dir, current_tab_text), # Suggest filename/dir
            filters,
            selected_filter # Set initial filter based on editor's current type
        )

        if path:
             # Ensure the correct extension is added if not typed by user
             _, ext = os.path.splitext(path)
             required_ext = ""
             if "(*.txt)" in selected_filter_out:
                 required_ext = ".txt"
             elif "(*.py)" in selected_filter_out:
                 required_ext = ".py"
             
             # Add extension if missing, based on the selected filter
             if not ext and required_ext:
                 path += required_ext
             elif ext.lower() != required_ext and required_ext:
                 # Optional: Warn user about extension mismatch or just force it? Forcing is simpler.
                 path = os.path.splitext(path)[0] + required_ext


             try:
                with open(path, "w", encoding='utf-8') as file: # Specify encoding
                    file.write(editor.text.toPlainText())

                # Update editor's details AFTER successful save
                editor.setFileDetails(path) # This sets path, extension, highlighter and resets modified flag
                index = self.tabs.currentIndex()
                self.tabs.setTabText(index, os.path.basename(path)) # Update tab title

                # Update combobox if saved type is different and supported
                if editor.file_extension in [".txt", ".py"]: # Check if extension is in combobox items
                    if self.fileTypeComboBox.currentText() != editor.file_extension:
                        self.fileTypeComboBox.setCurrentText(editor.file_extension)

             except Exception as e:
                QMessageBox.critical(self, "Error Saving File", f"Could not save file:\n{e}")


    def closeCurrentTab(self):
        index = self.tabs.currentIndex()
        if index != -1: # Check if there is a tab to close
            self.closeTab(index)


    def closeTab(self, index):
        editor = self.tabs.widget(index)
        # Ensure it's an editor widget we expect before checking properties
        if isinstance(editor, TextEditor):
            if editor.isModified:
                # Improved message box with file context
                filename = self.tabs.tabText(index).replace(" *", "")
                reply = QMessageBox.question(
                    self,
                    "Unsaved Changes",
                    f"Do you want to save changes made to '{filename}'?",
                    QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel, # Use standard options
                    QMessageBox.Save # Default button
                )

                if reply == QMessageBox.Save:
                    # Attempt to save. If save fails (e.g., user cancels Save As), DO NOT close.
                    if editor.path:
                         self.saveFile() # Try direct save first
                    else:
                         self.saveFileAs() # Trigger Save As dialog
                    # Check if it's still modified (Save As might have been cancelled)
                    if editor.isModified:
                         return # Don't close if save was cancelled/failed
                elif reply == QMessageBox.Cancel:
                    return # Don't close the tab
                # If Discard, proceed to remove tab

        # Remove the tab only if checks passed or weren't needed
        self.tabs.removeTab(index)
        
        # Optional: Close window if last tab is closed
        # if self.tabs.count() == 0:
        #    self.close()


    def currentEditor(self):
        # Return the current TextEditor widget, or None if no tabs or wrong widget type
        widget = self.tabs.currentWidget()
        if isinstance(widget, TextEditor):
            return widget
        return None

    # Slot to update syntax highlighting of the current tab when combobox changes
    def updateCurrentTabSyntax(self, extension):
        editor = self.currentEditor()
        if editor:
            editor.updateSyntaxHighlighting(extension)
            # Optional: If the file is unsaved/new, maybe mark it modified?
            # if not editor.path:
            #    editor.markUnsaved() # Indicate change might need saving


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec_())
