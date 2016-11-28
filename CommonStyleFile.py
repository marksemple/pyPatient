# if '.res/styleFile.txt' exists:
# load and check to see its the same.
# if okay, do nothing

# if doesn't exist:
# create one.

import os

def compareStyleFiles(location=''):

    styleFile = os.path.join(location, 'res/StyleSheet.txt')
    newStyle = getCommonStyleFile()

    try:
        with open(styleFile, 'r') as content_file:
            content = content_file.read()

        if content == newStyle:
            print('all up to date')
            return
    except:
        pass

    print('re-writing style file')
    fileObj = open(styleFile, 'w')
    fileObj.write(newStyle)
    fileObj.close()


def getCommonStyleFile():

    return """
QWidget {
    background-color: white;
    margin: 0pt;
    padding: 0pt;
    /*font: large "Arial"*/
    }

QMenuBar::item {
    background: transparent;
    color: black}
QMenuBar::item:selected {
    background: lightAccent;
    color: black}
QMenu::item:selected {
    background: lightAccent;
    color: black}

QToolBar {
    background: white}
QToolButton {
    background: white;
    border: none;
    border-radius: 4px;
    padding: 5px;
    margin: 1px}
QToolButton:hover, QPushButton:hover {
    background: lightAccent}
QToolButton:pressed, QPushButton:pressed {
    background: accentCol}
QPushButton, QComboBox {
    border: 1px solid lightBackground;
    margin: 2px;
    border-width: 1px;
    border-radius: 4px;
    padding: 5px;
    min-width: 100px;
    font-size: 9pt}

/* To Format: add Symbol for "Checked" */
QCheckBox {
    font-size: 10pt
}

QCheckBox::indicator {
        width: 12px;
        height: 12px;
        border: 2px solid midBackground;
        border-radius: 4px;
}

QCheckBox::indicator:checked {
        background-color: accentCol;
} /* URL to IM? */

QLineEdit {
    border: 1px solid lightBackground;
    border-radius: 4px;
    margin: 2px;
    padding: 4px}



QLabel {
    border-color: white;
    margin: 0px;
    padding: 0px;
    font-size: 10pt;
    min-width: 80px;
}
QLabel:selected {
    border-color: accentCol
}



QSlider {
    padding: 4px;
    margin: 4px;
}
QSlider::groove:vertical {
    border: 2px solid midBackground;
    background: white;
    border-radius: 6px;
    width: 8px;
}
QSlider::handle {
    border: 3px solid accentCol;
    background: lightAccent;
    border-radius: 9px;
    height: 16px;
    width: 18px;
    margin: 4px;
    margin-left: -6px;
    margin-right: -6px;
}

QComboBox::down-arrow {
image: url(./res/dropdown.png);
}
QComboBox::drop-down{
border: 1px solid accentCol;
border-radius: 2px;
background: lightAccent;
}

QTabWidget::pane {
    border: 2px solid accentCol}
QTabWidget::tab-bar {
    left: 12px;
    top: 2px}
QTabBar::tab {
    background: lightAccent;
    border: 2px solid accentCol;
    border-bottom-color: white; /* same as the pane color */
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    min-width: 80px;
    padding: 5px;
    font-size: 9pt}
QTabBar::tab:selected{
    background: white;
    border-color: accentCol;
    border-bottom-color: white; /* same as pane color */
}
QTabBar::tab:!selected {
    margin-top: 2px; /* make non-selected tabs look smaller */
    border-color: transparent;
    border-bottom-color: accentCol}
/* make use of negative margins for overlapping tabs */
QTabBar::tab:selected {
    /* expand/overlap to the left and right by 4px */
    margin-left: -4px;
    margin-right: -4px}
QTabBar::tab:first:selected {
    margin-left: 0; /* the first selected tab has nothing to overlap with on the left */
}
QTabBar::tab:last:selected {
    margin-right: 0; /* the last selected tab has nothing to overlap with on the right */
}
QTabBar::tab:only-one {
    margin: 0; /* if there is only one tab, we don't want overlapping margins */
}
        """



# if __name__ == "__main__":
#     compareStyleFiles()
