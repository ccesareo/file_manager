from Qt import QtCore, QtGui, QtWidgets


def apply_default_color_scheme():
    highlight_color = QtGui.QColor(103, 141, 178)
    bright_color = QtGui.QColor(200, 200, 200)
    light_color = QtGui.QColor(100, 100, 100)
    dark_color = QtGui.QColor(42, 42, 42)
    mid_color = QtGui.QColor(68, 68, 68)
    mid_light_color = QtGui.QColor(84, 84, 84)
    shadow_color = QtGui.QColor(21, 21, 21)

    base_color = mid_color
    text_color = bright_color
    disabled_button_color = QtGui.QColor(78, 78, 78)
    disabled_text_color = QtGui.QColor(128, 128, 128)
    alternate_base_color = QtGui.QColor(46, 46, 46)

    brightness_spread = 2.5

    if base_color.lightnessF() > 0.5:
        spread = 100 / brightness_spread
    else:
        spread = 100 * brightness_spread

    if highlight_color.lightnessF() > 0.6:
        highlighted_text_color = base_color.darker(spread * 2)
    else:
        highlighted_text_color = base_color.lighter(spread * 2)

    base_palette = QtGui.QPalette()
    base_palette.setBrush(QtGui.QPalette.Window, mid_color)
    base_palette.setBrush(QtGui.QPalette.WindowText, text_color)
    base_palette.setBrush(QtGui.QPalette.Foreground, bright_color)
    base_palette.setBrush(QtGui.QPalette.Base, dark_color)
    base_palette.setBrush(QtGui.QPalette.AlternateBase, alternate_base_color)
    base_palette.setBrush(QtGui.QPalette.ToolTipBase, base_color)
    base_palette.setBrush(QtGui.QPalette.ToolTipText, text_color)

    base_palette.setBrush(QtGui.QPalette.Text, text_color)
    base_palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Text, disabled_text_color)
    base_palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.WindowText, disabled_text_color)

    base_palette.setBrush(QtGui.QPalette.Button, light_color)
    base_palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Button, disabled_button_color)
    base_palette.setBrush(QtGui.QPalette.ButtonText, text_color)
    base_palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.ButtonText, disabled_text_color)
    base_palette.setBrush(QtGui.QPalette.BrightText, text_color)
    base_palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.BrightText, disabled_text_color)

    base_palette.setBrush(QtGui.QPalette.Light, light_color)
    base_palette.setBrush(QtGui.QPalette.Midlight, mid_light_color)
    base_palette.setBrush(QtGui.QPalette.Mid, mid_color)
    base_palette.setBrush(QtGui.QPalette.Dark, dark_color)
    base_palette.setBrush(QtGui.QPalette.Shadow, shadow_color)

    base_palette.setBrush(QtGui.QPalette.Highlight, highlight_color)
    base_palette.setBrush(QtGui.QPalette.HighlightedText, highlighted_text_color)

    tab_palette = QtGui.QPalette(base_palette)
    tab_palette.setBrush(QtGui.QPalette.Window, light_color)
    tab_palette.setBrush(QtGui.QPalette.Button, mid_color)

    preferred_styles = ["Plastique", "Fusion"]  # PySide has 'Plastique' while PySide2 has 'Fusion'
    available_styles = QtWidgets.QStyleFactory.keys()
    for style_name in (set(available_styles) & set(preferred_styles)):
        QtWidgets.QApplication.setStyle(style_name)
        break

    QtWidgets.QApplication.setPalette(base_palette)
    QtWidgets.QApplication.setPalette(tab_palette, "QTabBar")
    QtWidgets.QApplication.setPalette(tab_palette, "QTabWidget")
