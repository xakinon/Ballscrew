# -*- coding: utf-8 -*-
from PyQt5 import QtWidgets, QtCore, QtGui

class Model(QtCore.QAbstractItemModel):
    def __init__(self, parent_=None):
        super(Model, self).__init__(parent_)
        self.parent_ = parent_
        self.items = []
        self.columns = []
        
    def addColumns(self, list_):
        self.beginInsertColumns(QtCore.QModelIndex(), len(self.columns), len(self.columns) + len(list_) - 1)
        self.columns.extend(list_)
        self.endInsertColumns()
        
    def addItems(self, dicts):
        self.beginInsertRows(QtCore.QModelIndex(), len(self.items), len(self.items) + len(dicts) - 1)
        self.items.extend(dicts)
        self.endInsertRows()
        
    def columnCount(self, parent=QtCore.QModelIndex()):
        return len(self.columns)
        
    def data(self, index, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.EditRole or role == QtCore.Qt.DisplayRole:
            return self.items[ index.row() ].get( self.columns[index.column()], '' )
        return QtCore.QVariant()
        
    def flags(self, index):
        return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        
    def headerData(self, num, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            if int (num) >= len(self.columns):
                return ''
            else:
                return self.columns[num]
        
        if orientation == QtCore.Qt.Vertical and role == QtCore.Qt.DisplayRole:
            return num
        
    def index(self, row, column, parent):
        return self.createIndex(row, column, QtCore.QModelIndex())
        
    def parent(self, index):
        return QtCore.QModelIndex()
        
    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.items)
        
    def removeAllItems(self):
        self.beginRemoveRows(QtCore.QModelIndex(), 0, len(self.items) - 1)
        self.items = []
        self.endRemoveRows()
        
    def removeItem(self, row):
        self.beginRemoveRows(QtCore.QModelIndex(), row, row)
        del self.items[row]
        self.endRemoveRows()
        
    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if role == QtCore.Qt.EditRole:
            self.items[ index.row() ][ self.columns[index.column()] ] = value
            return True
        return False
        
class Delegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent=None):
        super(Delegate, self).__init__(parent)

    def createEditor(self, parent, option, index):
        return QtWidgets.QLineEdit(parent)

    def setEditorData(self, editor, index):
        value = index.model().data( index, QtCore.Qt.DisplayRole )
        editor.setText( str(value) )

    def setModelData(self, editor, model, index):
        model.setData( index, editor.text() )

class DictTableView(QtWidgets.QTableView):
    def __init__(self, parent=None):
        super(DictTableView, self).__init__(parent)

        # コンテキストメニュー設定
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.contextMenu)

    def addItem(self):
        # 最後に行追加
        self.model().addItems( [{}] )

    def contextMenu(self, point):
        # コンテキストメニュー作成と表示
        menu = QtWidgets.QMenu(self)
        menu.addAction('追加', self.addItem )
        menu.addAction('削除', self.removeSelectedItems )
        menu.exec_(self.mapToGlobal(point))
        
    def CtrlC(self):
        # 選択したセルをタブと改行で結合してクリップボードにセット
        selectedIndexes = self.selectedIndexes()
        modelData = selectedIndexes[0].model().data
        row = selectedIndexes[0].row()
        txt = ''

        for index in selectedIndexes:
            if not row == index.row():
                row = index.row()
                txt = txt[:-1] + '\n'
            txt = txt + str(modelData(index)) + '\t'
        txt = txt[:-1]
        QtWidgets.QApplication.clipboard().setText(txt)

    def CtrlV(self):
        # クリップボードの文字列を改行とタブなどで分割してtableviewに貼り付け
        selectedIndexes = self.selectedIndexes()
        index = selectedIndexes[0]
        model = index.model()
        clipboardText = QtWidgets.QApplication.clipboard().text()
        for r, line in enumerate(clipboardText.splitlines()):
            if r + index.row() >= len(model.items):
                model.addItems([{}])
            for c, cellData in enumerate(line.split()):
                if c + index.column() >= len(model.columns):
                    break
                inputIndex = model.index(r + index.row(), c + index.column(), QtCore.QModelIndex())
                model.setData(inputIndex, cellData.strip())
                model.dataChanged.emit(inputIndex, inputIndex)
        
    def removeSelectedItems(self):
        # 選択したセルの行を削除
        rows = { key.row():None for key in self.selectedIndexes() }
        for row in list( rows.keys() )[::-1]:
            self.model().removeItem( row )

if __name__ == '__main__':

    def myKeyPressEvent(e):
        # キーが押されたときのイベント
        if (e.modifiers() & QtCore.Qt.ControlModifier):
            if e.key() == QtCore.Qt.Key_C:
                tableView.CtrlC()
            if e.key() == QtCore.Qt.Key_V:
                tableView.CtrlV()
    
    import sys
    app = QtWidgets.QApplication(sys.argv)

    # mainwindow設定
    window = QtWidgets.QMainWindow()
    window.resize(600, 600)
    window.keyPressEvent = myKeyPressEvent

    # ui設定
    centralwidget = QtWidgets.QWidget(window)
    verticalLayout = QtWidgets.QVBoxLayout(centralwidget)

    # tableview設定
    tableView = DictTableView(centralwidget)
    model = Model()
    tableView.setModel(model)
    tableView.setItemDelegate(Delegate())

    # レイアウト
    verticalLayout.addWidget(tableView)
    window.setCentralWidget(centralwidget)

    # モデルにテストデータをセット
    model.addColumns(['C1','C2'])
    model.addItems( [ {'C1':'test11', 'C2':'test12'}, \
                      {'C1':'test21', 'C2':'test22'}, \
                      {'C1':123, 'C2':0.456} ] )

    window.show()
    app.exec_()