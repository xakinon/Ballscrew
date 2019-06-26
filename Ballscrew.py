# -*- coding: utf-8 -*-
import configparser
import csv
import sys
from PyQt5 import QtWidgets, QtCore
#import qdarkstyle

from mainwindow import Ui_MainWindow
from model import Model, Delegate, DictTableView
from calicurate import Calicurate

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        
        # UI設定
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # iniファイル読み込み
        self.iniflename = 'settings.ini'
        self.inifile = configparser.ConfigParser()
        self.inifile.read(self.iniflename, encoding='utf8')

        # デーブル設定
        self.model = {'conditions':Model()}
        self.proxyModel = {}
        self.tableView = {'conditions':self.ui.tableView_conditions}
        keys = ['ballscrew', 'motor', 'coupling', 'result']
        tableViews = [self.ui.tableView_ballscrew, self.ui.tableView_motor, self.ui.tableView_coupling, self.ui.tableView_result]
        for key, tableView in zip(keys, tableViews):
            self.model[key] = Model()
            self.proxyModel[key] = QtCore.QSortFilterProxyModel()
            self.tableView[key] = tableView
            self.proxyModel[key].setSourceModel(self.model[key])
            self.tableView[key].setModel(self.proxyModel[key])
            self.tableView[key].setItemDelegate(Delegate())
            self.tableView[key].setAlternatingRowColors(True)
            self.tableView[key].setSortingEnabled(True)

        # csvのデータをモデルに追加
        for partname in ['ballscrew', 'motor', 'coupling']:
            with open(partname + '.csv', encoding='shift_jis') as f:
                dr = csv.DictReader(f)
                dicts = []
                for row in dr:
                    dict_ = {}
                    for key in row:
                        try:
                            dict_[key] = float( row[key] )
                        except:
                            dict_[key] = row[key]
                    dicts.append( dict_ )
            self.model[partname].addColumns( dicts[0].keys() )
            self.model[partname].addItems( dicts )

        # iniファイルから条件テーブルの設定取得
        self.tableView['conditions'].setModel(self.model['conditions'])
        self.tableView['conditions'].setItemDelegate(Delegate())
        self.tableView['conditions'].setColumnWidth(0, 80)
        self.tableView['conditions'].setColumnWidth(1, 30)
        columns = self.inifile.get('conditions','columns').splitlines()
        items = []
        for i in range(1000):
            try:
                vals = self.inifile.get( 'conditions', 'items_{:0=3}'.format(i) ).splitlines()
                item = { key:val for key, val in zip(columns, vals) }
                items.append(item)
            except:
                break
        self.model['conditions'].addColumns( columns )
        self.model['conditions'].addItems( items )

        # ツールチップ
        #self.ui.doubleSpinBox_load_coefficient.setToolTip(self.inifile.get('tooltips', 'doubleSpinBox_load_coefficient'))

        # イベントスロット
        self.ui.pushButton_calicurate.clicked.connect(self.calculate)
        #self.ui.plainTextEdit_narrow.textChanged.connect(self.filterChanged)
        #self.ui.comboBox_narrow.currentIndexChanged.connect(self.comboBoxCurrentIndexChanged)

        '''
    def filterChanged(self):
        regExp = QtCore.QRegExp( # 正規表現作成
            self.ui.plainTextEdit_narrow.toPlainText(), # 文字列
            QtCore.Qt.CaseSensitive, # 大文字、小文字を区別
            QtCore.QRegExp.RegExp2) # 文字列の扱い
        self.proxyModel['search'].setFilterRegExp(regExp) # 正規表現セット

    def comboBoxCurrentIndexChanged(self):
        if self.ui.comboBox_narrow.count() < 1:
            return # comboBoxにアイテムが無ければ何もしない
        keyIndex = self.model['search'].columns.index( self.ui.comboBox_narrow.currentText() )
        self.proxyModel['search'].setFilterKeyColumn( keyIndex )
        self.filterChanged()
        '''

    def calculate(self):
        conditions = {}
        for item in self.model['conditions'].items:
            try:
                conditions[item['項目']] = float(item['値'])
            except:
                conditions[item['項目']] = item['値']
        
        calicurate = Calicurate(conditions, self.model['ballscrew'].items, self.model['motor'].items, self.model['coupling'].items)
        calicurate.commit()
        self.model['result'].removeAllItems()
        if len( calicurate.dicts ) == 0:
            return
        if len( self.model['result'].columns ) == 0:
            self.model['result'].addColumns(calicurate.columns)
        self.model['result'].addItems(calicurate.dicts)

    def keyPressEvent(self, e):

        if (e.modifiers() & QtCore.Qt.ControlModifier):
            # Ctrlキーが押されたら
            
            # アクティブなtableViewを取得
            for tv in self.findChildren(QtWidgets.QTableView):
                if tv.hasFocus():
                    tableView = tv
                    break
            
            if e.key() == QtCore.Qt.Key_C:
                tableView.CtrlC()

            if e.key() == QtCore.Qt.Key_V:
                tableView.CtrlV()
                
            if e.key() == QtCore.Qt.Key_U:
                sourceModel = tableView.model().sourceModel()
                columns = sourceModel.columns
                items = sourceModel.items
                header = '\t'.join( columns ) + '\n'
                rows = [ '\t'.join( [ str(item[column]) for column in columns ] ) for item in items ]
                txt = header + '\n'.join( rows )
                QtWidgets.QApplication.clipboard().setText(txt[:-1])


def main():
    app = QtWidgets.QApplication(sys.argv)
    #app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    window = MainWindow()
    window.show()
    #sys.exit(app.exec_())
    app.exec_()
    
if __name__ == '__main__':
    main()