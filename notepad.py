import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTextEdit, QFileDialog, QAction, QTabWidget, QWidget,
                             QVBoxLayout, QToolBar, QMessageBox, QComboBox)
from PyQt5.QtGui import QFont, QColor, QSyntaxHighlighter, QTextCharFormat, QKeySequence
from PyQt5.QtCore import Qt, QRegularExpression


class TextHighlighter(QSyntaxHighlighter):
    def __init__(self, parent, file_extension):
        super(TextHighlighter, self).__init__(parent)
        self.highlightingRules = []
        self.file_extension = file_extension

        if self.file_extension == ".py":
            keywordFormat = QTextCharFormat()
            keywordFormat.setForeground(QColor("blue"))
            keywords = ["def", "class", "return", "if", "else", "try", "except", "import", "from", "as", "with"]
            self.highlightingRules += [(QRegularExpression(f"\\b{keyword}\\b"), keywordFormat) for keyword in keywords]

    def highlightBlock(self, text):
        for pattern, fmt in self.highlightingRules:
            matches = pattern.globalMatch(text)
            while matches.hasNext():
                match = matches.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)


class TextEditor(QWidget):
    def __init__(self, parent=None):
        super(TextEditor, self).__init__(parent)
        layout = QVBoxLayout(self)
        self.text = QTextEdit(self)
        self.text.setFont(QFont("Roboto Mono", 12))
        self.text.setStyleSheet("background-color: #1E1E1E; color: #E0E0E0; padding: 10px; border-radius: 5px;")
        self.path = ""
        self.file_extension = ""
        self.highlighter = None
        layout.addWidget(self.text)
        self.setLayout(layout)
        self.isModified = False
        self.text.textChanged.connect(self.markUnsaved)

    def setFileExtension(self, extension):
        self.file_extension = extension
        self.highlighter = TextHighlighter(self.text.document(), self.file_extension)

    def markUnsaved(self):
        if not self.isModified:
            self.isModified = True
            parent = self.parentWidget().parentWidget()
            if parent and isinstance(parent, QTabWidget):
                index = parent.indexOf(self.parentWidget())
                currentText = parent.tabText(index)
                if not currentText.endswith(" *"):
                    parent.setTabText(index, f"{currentText} *")


class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Google Chromebook Text Clone")
        self.resize(800, 600)
        self.setStyleSheet("background-color: #181818; color: #E0E0E0;")

        self.tabs = QTabWidget(self)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.closeTab)
        self.tabs.setMovable(True)
        self.tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #444; } "
                                "QTabBar::tab { background: #2A2A2A; padding: 8px; border-radius: 5px; } "
                                "QTabBar::tab:selected { background: #3A3A3A; font-weight: bold; }")
        self.setCentralWidget(self.tabs)
        self.createActions()
        self.createToolbar()
        self.createShortcuts()

    def createActions(self):
        self.newAction = QAction("New", self)
        self.newAction.triggered.connect(self.newFile)

        self.openAction = QAction("Open", self)
        self.openAction.triggered.connect(self.openFile)

        self.saveAction = QAction("Save", self)
        self.saveAction.triggered.connect(self.saveFile)

        self.saveAsAction = QAction("Save As", self)
        self.saveAsAction.triggered.connect(self.saveFileAs)

        self.closeAction = QAction("Close Tab", self)
        self.closeAction.triggered.connect(lambda: self.closeTab(self.tabs.currentIndex()))

    def createToolbar(self):
        toolbar = QToolBar(self)
        toolbar.setStyleSheet("background-color: #1E1E1E; color: #E0E0E0; padding: 5px; border-radius: 5px;")
        self.fileTypeComboBox = QComboBox()
        self.fileTypeComboBox.addItems([".txt", ".py"])
        toolbar.addAction(self.newAction)
        toolbar.addAction(self.openAction)
        toolbar.addAction(self.saveAction)
        toolbar.addAction(self.saveAsAction)
        toolbar.addAction(self.closeAction)
        toolbar.addWidget(self.fileTypeComboBox)
        self.addToolBar(toolbar)

    def createShortcuts(self):
        self.newAction.setShortcut(QKeySequence("Ctrl+N"))
        self.openAction.setShortcut(QKeySequence("Ctrl+O"))
        self.saveAction.setShortcut(QKeySequence("Ctrl+S"))
        self.saveAsAction.setShortcut(QKeySequence("Ctrl+Shift+S"))
        self.closeAction.setShortcut(QKeySequence("Ctrl+W"))

    def newFile(self):
        editor = TextEditor(self)
        index = self.tabs.addTab(editor, "Untitled")
        self.tabs.setCurrentIndex(index)

    def openFile(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "Text Files (*.txt);;Python Files (*.py);;All Files (*)")
        if path:
            with open(path, "r") as file:
                content = file.read()
                editor = TextEditor(self)
                editor.text.setText(content)
                editor.path = path
                extension = ".py" if path.endswith(".py") else ".txt"
                editor.setFileExtension(extension)
                index = self.tabs.addTab(editor, path.split("/")[-1])
                self.tabs.setCurrentIndex(index)

    def saveFile(self):
        editor = self.currentEditor()
        if editor and editor.path:
            with open(editor.path, "w") as file:
                file.write(editor.text.toPlainText())
            editor.isModified = False
            index = self.tabs.currentIndex()
            self.tabs.setTabText(index, editor.path.split("/")[-1])
        else:
            self.saveFileAs()

    def saveFileAs(self):
        editor = self.currentEditor()
        path, _ = QFileDialog.getSaveFileName(self, "Save File", "", "Text Files (*.txt);;Python Files (*.py);;All Files (*)")
        if path:
            # Add default .txt if no extension provided
            if not path.endswith(".txt") and not path.endswith(".py"):
                path += ".txt"
            
            with open(path, "w") as file:
                file.write(editor.text.toPlainText())
            editor.path = path
            editor.isModified = False
            self.tabs.setTabText(self.tabs.currentIndex(), path.split("/")[-1])

    def closeTab(self, index):
        editor = self.tabs.widget(index)
        if editor.isModified:
            reply = QMessageBox.question(self, "Unsaved Changes", "Do you want to save changes?", 
                                         QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Yes)
            if reply == QMessageBox.Yes:
                self.saveFile()
            elif reply == QMessageBox.Cancel:
                return
        self.tabs.removeTab(index)

    def currentEditor(self):
        return self.tabs.currentWidget()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec_())

